"""Additive, idempotent upgrade of pre-research SQLite/PostgreSQL databases."""
from sqlalchemy import inspect, text
from app.core.database import Base


def upgrade_schema(engine):
    # Import registers all models before create_all. Existing rows are retained.
    from app.models import models  # noqa: F401
    with engine.begin() as connection:
        if connection.dialect.name == 'postgresql':
            # Serialize concurrent app-worker migrations for this database.
            connection.execute(text('SELECT pg_advisory_xact_lock(72819346)'))
        Base.metadata.create_all(connection)
        existing = {c['name'] for c in inspect(connection).get_columns('threat_analysis_records')}
        columns = {
            'attacker_state_probs': 'JSON',
            'adaptation_score': 'FLOAT DEFAULT 0',
            'response_effectiveness': 'FLOAT DEFAULT 0',
            'attacker_state': "VARCHAR DEFAULT 'UNKNOWN'",
        }
        for name, definition in columns.items():
            if name not in existing:
                connection.execute(text(f'ALTER TABLE threat_analysis_records ADD COLUMN {name} {definition}'))
