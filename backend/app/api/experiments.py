from fastapi import APIRouter, Depends, Query
from app.core.security import require_role
import math
from app.services.orchestrator import orchestrator
from research.simulation import initial_profile, run_episode

router = APIRouter(prefix="/api/experiments", tags=["Research"],
                   dependencies=[Depends(require_role(["Admin", "Analyst"]))])


@router.post("/run-adaptive-ablation")
def run_time_series_experiment(user_id: int = Query(1, ge=0, le=2147483647)):
    """Run an isolated, reproducible closed-loop attacker/defender demonstration."""
    def score(features):
        scaled = orchestrator.feature_pipeline.transform(features)
        results = orchestrator.ml_engine.evaluate(scaled)
        return orchestrator.ml_engine.compute_risk_score(
            results['iforest_score'], results['ocsvm_score'], features)

    summary, traces = run_episode(
        risk_function=score, variant='Full SentinelAI', seed=max(0, int(user_id)),
        turns=8, initial=initial_profile(max(0, int(user_id))),
        metrics=orchestrator.game_engine.metrics)
    summary = {key: (None if isinstance(value, float) and not math.isfinite(value) else value)
               for key, value in summary.items()}
    return {
        'status': 'Experiment complete',
        'summary': summary,
        'time_series_data': [{
            'turn': row['turn'], 'strategy': row['current_attacker_state'],
            'defense': row['defence'], 'risk': row['current_risk'],
            'AAS': row['aas'], 'RES': row['res'],
            'previous_defence': row['previous_defence'],
            'previous_behaviour': row['previous_behaviour'],
            'current_behaviour': row['current_behaviour'],
            'successful_malicious_actions': row['successful_malicious_actions'],
        } for row in traces],
    }
