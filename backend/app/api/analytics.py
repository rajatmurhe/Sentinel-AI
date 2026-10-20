from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_role
from app.models.models import User, ActivityLog, Alert, Incident, ThreatAnalysisRecord, ResearchInteraction
from app.schemas.schemas import SimulationTrigger
from app.services.orchestrator import orchestrator
from app.ml.adaptive_attacker import AdaptiveAttacker
from research.simulation import initial_profile

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/dashboard-stats")
def get_dashboard_stats(db: Session = Depends(get_db), current_user=Depends(require_role(["Admin", "Analyst"]))):
    total_users = db.query(User).count()
    total_activities = db.query(ActivityLog).count()
    total_alerts = db.query(Alert).count()
    total_incidents = db.query(Incident).count()

    latest_assessment = db.query(ThreatAnalysisRecord).order_by(ThreatAnalysisRecord.timestamp.desc()).first()
    avg_risk = 0.0
    records = db.query(ThreatAnalysisRecord).all()
    if records:
        avg_risk = round(sum(r.risk_score for r in records) / len(records), 2)

    interaction = (db.query(ResearchInteraction)
                   .filter(ResearchInteraction.threat_record_id == latest_assessment.id).first()
                   if latest_assessment else None)
    return {
        "model_source": "synthetic demonstration detector",
        "enforcement_mode": "decision support / simulated enforcement",
        "total_users": total_users,
        "total_activities": total_activities,
        "total_alerts": total_alerts,
        "total_incidents": total_incidents,
        "average_risk": avg_risk,
        "latest_assessment": {
            "risk_score": latest_assessment.risk_score if latest_assessment else 0,
            "action": latest_assessment.game_action if latest_assessment else "ALLOW",
            "shap_attributions": latest_assessment.shap_attributions if latest_assessment else {},
            "aas": latest_assessment.adaptation_score if latest_assessment else 0,
            "res": latest_assessment.response_effectiveness if latest_assessment else 0,
            "res_available": interaction.res_available if interaction else False,
            "previous_defence": interaction.previous_defence if interaction else "UNKNOWN",
            "attacker_state": latest_assessment.attacker_state if latest_assessment else "UNKNOWN"
        }
    }

@router.post("/simulate-threat")
def simulate_threat(payload: SimulationTrigger, db: Session = Depends(get_db), current_user=Depends(require_role(["Admin", "Analyst"]))):
    if db.get(User, payload.user_id) is None:
        raise HTTPException(status_code=404, detail="Target user does not exist")
    attacker = AdaptiveAttacker(payload.seed, initial_profile(payload.seed))
    if payload.scenario == 'DATA_EXFILTRATION':
        attacker = AdaptiveAttacker(payload.seed)
    results = []
    previous_action = None
    for i in range(payload.iterations):
        if payload.scenario in ('ADAPTIVE_EVASION', 'DATA_EXFILTRATION'):
            sample = attacker.observe_and_adapt(previous_action) if previous_action else dict(attacker.behaviour)
            action_name = attacker.strategy
        else:
            sample = dict(login_hour=2. if payload.scenario == 'ABNORMAL_HOURS' else 11.,
                          files_accessed=10., sensitive_files_accessed=0., bytes_transferred_mb=15.,
                          failed_logins=0., privilege_level=0., session_duration_min=180.)
            action_name = "ROUTINE_ACCESS"
        db.add(ActivityLog(user_id=payload.user_id, action_type=action_name,
                           bytes_transferred=sample['bytes_transferred_mb'],
                           is_sensitive_file=sample['sensitive_files_accessed'] > 0,
                           failed_attempts=int(sample['failed_logins']),
                           privilege_level=int(sample['privilege_level']),
                           session_duration_sec=sample['session_duration_min'] * 60))
        res = orchestrator.analyze_event(payload.user_id, sample, db)
        previous_action = res['game_action']
        res['behaviour'] = sample
        res['turn'] = i + 1
        if payload.scenario in ('ADAPTIVE_EVASION', 'DATA_EXFILTRATION'):
            res['simulated_attacker_state'] = attacker.strategy
            res['simulated_outcome'] = attacker.enforce(previous_action)
        results.append(res)
    return {"scenario": payload.scenario, "seed": payload.seed, "executions": results,
            "source": "synthetic action-conditioned demonstration; not CERT evaluation"}
