"""Finite, pure-strategy adaptive Stackelberg game (not a Bayesian game).

Defender commits first; follower maximizes its utility for each commitment.
Ties in follower utility use a pessimistic tie break (least defender utility).
Utilities and success estimates are explicit modelling assumptions, not fitted CERT facts.
"""
import numpy as np
from app.services.attacker_adaptation import AttackerAdaptationEngine, RESPONSES

ACTIONS = ('ALLOW', 'MONITOR', 'STEP_UP_AUTH', 'RESTRICT', 'REVOKE')
STRATEGIES = ('AGGRESSIVE_EXFILTRATION', 'STEALTH_EXFILTRATION', 'PROBING', 'ABORT')
COST = np.array([0., .025, .08, .20, .42])
# Estimated probability that an attempted strategy succeeds under each defence.
SUCCESS = np.array([[.98, .95, .90, 0.], [.72, .88, .65, 0.],
                    [.50, .64, .18, 0.], [.08, .35, .25, 0.], [.005, .015, .02, 0.]])
DAMAGE = np.array([1., .65, .35, 0.])
ATTACK_COST = np.array([.12, .10, .06, 0.])


class AdaptiveStackelbergGameEngine:
    def __init__(self, metrics=None):
        self.metrics = metrics or AttackerAdaptationEngine()
        self.strategies = list(STRATEGIES)

    def calculate_attacker_state_probs(self, raw_features):
        # Compatibility payload: categorical evidence, not Bayesian posteriors.
        state = self.metrics.classify_state(raw_features)
        return {state: 1.}

    def calculate_adaptation_score(self, current_features, prev_features, prev_action):
        return self.metrics.calculate_adaptation_score(current_features, prev_features, prev_action)

    def calculate_effectiveness_score(self, current_risk, prev_risk, prev_action,
                                      current_features=None, prev_features=None):
        return self.metrics.calculate_effectiveness_score(current_risk, prev_risk, prev_action,
                                                          current_features, prev_features)

    def resolve_optimal_defense(self, risk_score, attacker_state, aas, res,
                                previous_defence='UNKNOWN', response_available=True):
        if isinstance(attacker_state, dict):
            attacker_state = max(attacker_state, key=attacker_state.get)
        risk = float(np.clip(risk_score / 100., 0., 1.))
        aas, res = float(np.clip(aas, 0., 1.)), float(np.clip(res, 0., 1.))
        history = previous_defence in RESPONSES and response_available
        failure = (1. - res) if history else 0.
        # Modulate failure by current risk: benign persistence alone is not an attack.
        urgency = float(np.clip(.65 * risk + .20 * aas + .15 * failure * risk, 0., 1.))
        success = SUCCESS.copy()
        if history:
            success[:, 1] = np.clip(success[:, 1] + .15 * aas * (1. - success[:, 1]), 0, 1)
            idx = ACTIONS.index(previous_defence)
            success[idx, :3] += .10 * failure * (1. - success[idx, :3])
        preference = np.ones(4)
        if attacker_state in STRATEGIES:
            preference[STRATEGIES.index(attacker_state)] = 1.25
        attacker_utilities = success * DAMAGE * preference - ATTACK_COST - (1. - success) * .15
        attacker_utilities[:, 3] = 0.  # Abort: zero gain/cost, no malicious attempt.
        defender_utilities = urgency * (1. - success * DAMAGE) - COST[:, None] * (1. - .5 * risk)
        if previous_defence in ACTIONS:
            defender_utilities -= np.array([0. if a == previous_defence else .005 for a in ACTIONS])[:, None]
        responses, utilities, table = {}, {}, {}
        for i, action in enumerate(ACTIONS):
            best = np.flatnonzero(np.isclose(attacker_utilities[i], attacker_utilities[i].max()))
            j = min(best, key=lambda k: defender_utilities[i, k])
            responses[action] = STRATEGIES[j]
            utilities[action] = float(defender_utilities[i, j])
            table[action] = {strategy: {'attacker': float(attacker_utilities[i, k]),
                                       'defender': float(defender_utilities[i, k])}
                             for k, strategy in enumerate(STRATEGIES)}
        selected = max(ACTIONS, key=lambda a: utilities[a])
        return {'selected_action': selected, 'expected_utility': utilities[selected],
                'action_distribution': utilities, 'defender_utilities': utilities,
                'attacker_best_responses': responses, 'utility_table': table, 'urgency': urgency}
