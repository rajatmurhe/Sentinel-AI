"""Paired seeded, closed-loop stress tests. Simulator results are NOT CERT outcomes."""
from time import perf_counter
import numpy as np
from app.ml.adaptive_attacker import AdaptiveAttacker
from app.services.attacker_adaptation import AttackerAdaptationEngine
from research.protocol import decide


def run_episode(risk_function, variant='Full SentinelAI', seed=0, turns=8, initial=None, metrics=None):
    metrics = metrics or AttackerAdaptationEngine()
    attacker = AdaptiveAttacker(seed, initial)
    previous, traces = None, []
    for turn in range(1, turns+1):
        previous_defence = previous['action'] if previous else 'UNKNOWN'
        if previous:
            behaviour = attacker.observe_and_adapt(previous_defence)
        else:
            behaviour = dict(attacker.behaviour)
        started = perf_counter()
        risk = 0. if attacker.aborted else float(risk_function(behaviour))
        decision = decide(variant, risk, behaviour, previous, metrics)
        response_ms = (perf_counter() - started) * 1000.
        outcome = attacker.enforce(decision['action'])
        traces.append({
            'turn': turn, 'variant': variant, 'seed': seed,
            'previous_behaviour': previous['behaviour'] if previous else {},
            'current_behaviour': behaviour, 'previous_defence': previous_defence,
            'previous_risk': previous['risk'] if previous else None,
            'current_risk': risk, 'current_attacker_state': attacker.strategy,
            'inferred_attacker_state': decision['state'], 'defence': decision['action'],
            'aas': decision['aas'], 'res': decision['res'], 'res_available': decision['res_available'],
            'res_components': decision['res_components'], 'response_ms': response_ms,
            'game': decision['game'], **outcome,
        })
        previous = {'behaviour': behaviour, 'risk': risk, 'action': decision['action']}
    attempts = sum(r['malicious_attempts'] for r in traces)
    successes = sum(r['successful_malicious_actions'] for r in traces)
    available_res = [r['res'] for r in traces if r['res_available']]
    # Each next observation follows the previous defence and the attacker's
    # resulting adaptation. Average those per-transition risk changes so the
    # metric does not collapse to an initial-versus-terminal comparison.
    post_response = [r['current_risk'] for r in traces[1:]]
    transition_reductions = [
        float(np.clip((traces[i-1]['current_risk'] - traces[i]['current_risk']) /
                      max(traces[i-1]['current_risk'], 1e-9), -1., 1.))
        for i in range(1, len(traces))
    ]
    adaptive_attempts = [r for r in traces[1:] if r['aas'] > 0 and r['malicious_attempts'] > 0]
    summary = {
        'attack_success_rate': successes / max(attempts, 1),
        'episode_success': float(successes > 0), 'successful_malicious_actions': successes,
        'malicious_attempts': attempts, 'exfiltrated_mb': sum(r['exfiltrated_mb'] for r in traces),
        'risk_after_defence': float(np.mean(post_response)) if post_response else float('nan'),
        'risk_reduction': float(np.mean(transition_reductions)) if transition_reductions else float('nan'),
        'aas': float(np.mean([r['aas'] for r in traces[1:]])) if turns > 1 else float('nan'),
        'res': float(np.mean(available_res)) if available_res else float('nan'),
        'res_observations': len(available_res),
        'adaptation_handling': float(np.mean([r['successful_malicious_actions'] == 0 for r in adaptive_attempts])) if adaptive_attempts else float('nan'),
        'response_ms': float(np.mean([r['response_ms'] for r in traces])),
    }
    return summary, traces


def initial_profile(seed):
    rng = np.random.default_rng(seed)
    # Start with a low-volume foothold so policies can respond over multiple
    # turns. All ablation arms receive the same seed-specific profile.
    return {'login_hour': float(rng.choice([2, 11, 14, 22])),
            'files_accessed': float(rng.integers(10, 20)),
            'sensitive_files_accessed': float(rng.choice([0, 0, 1])),
            'bytes_transferred_mb': float(rng.uniform(10, 55)),
            'failed_logins': 0.,
            'privilege_level': 0.,
            'session_duration_min': float(rng.integers(120, 240))}
