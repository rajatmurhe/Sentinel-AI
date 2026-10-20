"""Exercise real auth, migrated storage, dashboard, simulations and artifacts.

Default SQLite is isolated in a temp directory. Set SENTINEL_TEST_DATABASE_URL to
an explicitly disposable PostgreSQL database for the same suite.
"""
import os
import tempfile
from pathlib import Path
import pytest
from sqlalchemy import create_engine, text, inspect
from fastapi.testclient import TestClient

TEMP = tempfile.TemporaryDirectory(prefix='sentinel-tests-')
os.environ['DATABASE_URL'] = os.environ.get('SENTINEL_TEST_DATABASE_URL',f'sqlite:///{TEMP.name}/test.db')
os.environ['SECRET_KEY'] = 'isolated-integration-test-secret'
from app.main import app
from app.core.database import engine, SessionLocal
from app.core.migrations import upgrade_schema
from app.models.models import ResearchInteraction, ThreatAnalysisRecord


def test_existing_schema_migration_retains_rows():
    legacy = create_engine(f'sqlite:///{TEMP.name}/legacy.db')
    with legacy.begin() as conn:
        conn.execute(text('CREATE TABLE threat_analysis_records (id INTEGER PRIMARY KEY, user_id INTEGER, raw_features JSON)'))
        conn.execute(text("INSERT INTO threat_analysis_records VALUES (1,1,'{}')"))
    upgrade_schema(legacy); upgrade_schema(legacy)
    assert {'attacker_state_probs','adaptation_score','response_effectiveness','attacker_state'} <= {c['name'] for c in inspect(legacy).get_columns('threat_analysis_records')}
    with legacy.connect() as conn:
        assert conn.execute(text('SELECT COUNT(*) FROM threat_analysis_records')).scalar() == 1
    legacy.dispose()


def test_complete_dashboard_flow():
    with TestClient(app) as client:
        assert client.get('/health').status_code == 200
        assert client.get('/api/research/results').status_code == 401
        assert client.post('/api/experiments/run-adaptive-ablation').status_code == 401
        login = client.post('/api/auth/login',data={'username':'admin','password':'AdminSecurePass123!'})
        assert login.status_code == 200,login.text
        headers = {'Authorization':f"Bearer {login.json()['access_token']}"}
        vector = dict(login_hour=17.,files_accessed=33.,sensitive_files_accessed=3.,bytes_transferred_mb=175.,failed_logins=1.,privilege_level=1.,session_duration_min=123.)
        response = client.post('/api/activities/analyze',json=vector,headers=headers)
        assert response.status_code == 200,response.text
        with SessionLocal() as db:
            stored = db.query(ResearchInteraction).order_by(ResearchInteraction.id.desc()).first()
            assert stored.current_behaviour == vector
        invalid = dict(vector,login_hour=25)
        assert client.post('/api/activities/analyze',json=invalid,headers=headers).status_code == 422
        response = client.post('/api/analytics/simulate-threat',json={'user_id':3,'scenario':'ADAPTIVE_EVASION','iterations':8,'seed':42},headers=headers)
        assert response.status_code == 200,response.text
        turns = response.json()['executions']
        assert len(turns)==8
        assert any(t['adaptive_metrics']['adaptation_score_aas']>0 for t in turns[1:])
        for before,after in zip(turns,turns[1:]):
            assert after['adaptive_metrics']['previous_defence']==before['game_action']
        with SessionLocal() as db:
            interactions = db.query(ResearchInteraction).filter(ResearchInteraction.user_id==3).order_by(ResearchInteraction.id.desc()).limit(8).all()[::-1]
            for before,after in zip(interactions,interactions[1:]):
                assert after.previous_behaviour==before.current_behaviour
        stats = client.get('/api/analytics/dashboard-stats',headers=headers)
        assert stats.status_code==200 and stats.json()['latest_assessment']['res_available']
        experiment = client.post('/api/experiments/run-adaptive-ablation?user_id=2',headers=headers)
        assert experiment.status_code==200,experiment.text
        assert len(experiment.json()['time_series_data'])==8
        results = client.get('/api/research/results',headers=headers)
        assert results.status_code==200,results.text
        assert len(results.json()['detection'])==6
        assert client.get('/api/research/files/research-results.png',headers=headers).headers['content-type']=='image/png'
        assert client.get('/api/research/files/not-allowed.txt',headers=headers).status_code==404
        assert client.get('/').status_code==200


def test_postgresql_legacy_upgrade():
    if engine.dialect.name != 'postgresql':
        pytest.skip('Run with a disposable PostgreSQL database to test this upgrade')
    import uuid
    schema = 'sentinel_legacy_' + uuid.uuid4().hex
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA {schema}'))
    legacy = create_engine(os.environ['DATABASE_URL'],connect_args={'options':f'-csearch_path={schema}'})
    try:
        with legacy.begin() as conn:
            conn.execute(text('CREATE TABLE threat_analysis_records (id SERIAL PRIMARY KEY, user_id INTEGER, raw_features JSON)'))
            conn.execute(text("INSERT INTO threat_analysis_records(user_id,raw_features) VALUES (1,'{}')"))
        upgrade_schema(legacy); upgrade_schema(legacy)
        with legacy.connect() as conn:
            assert conn.execute(text('SELECT COUNT(*) FROM threat_analysis_records')).scalar()==1
            assert conn.execute(text('SELECT attacker_state FROM threat_analysis_records')).scalar()=='UNKNOWN'
    finally:
        legacy.dispose()
        with engine.begin() as conn:
            conn.execute(text(f'DROP SCHEMA {schema} CASCADE'))
