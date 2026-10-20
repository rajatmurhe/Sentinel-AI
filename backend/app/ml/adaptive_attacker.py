"""Closed-loop simulation environment. These are explicit simulator assumptions.

The attacker observes the last action. Environment enforcement parameters are
separate from the defender's estimated payoff table, to avoid identical oracles.
"""
import numpy as np


class AdaptiveAttacker:
    def __init__(self, seed=42, initial=None):
        self.rng = np.random.default_rng(seed)
        self.behaviour = initial or dict(login_hour=2., files_accessed=85., sensitive_files_accessed=20.,
            bytes_transferred_mb=1600., failed_logins=2., privilege_level=2., session_duration_min=360.)
        self.strategy = 'AGGRESSIVE_EXFILTRATION'
        self.aborted = False

    def observe_and_adapt(self, previous_defence):
        b = dict(self.behaviour)
        if self.aborted:
            return dict(b)
        if previous_defence == 'REVOKE':
            self.aborted = True
            self.strategy = 'ABORT'
            for k in b:
                b[k] = 12. if k == 'login_hour' else 0.
        elif previous_defence == 'RESTRICT':
            self.strategy = 'STEALTH_EXFILTRATION'
            b.update(bytes_transferred_mb=max(5., b['bytes_transferred_mb'] * self.rng.uniform(.12, .30)),
                     sensitive_files_accessed=max(1., b['sensitive_files_accessed'] * .35),
                     files_accessed=max(3., b['files_accessed'] * .35), login_hour=float(self.rng.uniform(10, 16)),
                     failed_logins=0., privilege_level=1., session_duration_min=min(720., b['session_duration_min'] * 1.4))
        elif previous_defence == 'STEP_UP_AUTH':
            self.strategy = 'PROBING'
            b.update(failed_logins=float(self.rng.integers(3, 7)), bytes_transferred_mb=b['bytes_transferred_mb'] * .3,
                     sensitive_files_accessed=max(1., b['sensitive_files_accessed'] * .5), login_hour=13., privilege_level=0.)
        elif previous_defence == 'MONITOR':
            self.strategy = 'STEALTH_EXFILTRATION'
            b.update(bytes_transferred_mb=b['bytes_transferred_mb'] * .7,
                     sensitive_files_accessed=max(1., b['sensitive_files_accessed'] * .8),
                     files_accessed=max(2., b['files_accessed'] * .75), login_hour=14., failed_logins=0.)
        else:
            self.strategy = 'AGGRESSIVE_EXFILTRATION'
            # When access remains open, escalate a small foothold into visible
            # exfiltration. This action-conditioned transition makes ALLOW
            # observably different from the other defender responses.
            b.update(bytes_transferred_mb=max(20., b['bytes_transferred_mb'] * self.rng.uniform(1.45, 1.8)),
                     files_accessed=b['files_accessed'] + float(self.rng.integers(2, 7)),
                     sensitive_files_accessed=min(20., b['sensitive_files_accessed'] + 1.),
                     login_hour=float(self.rng.choice([2., 22.])))
        self.behaviour = b
        return dict(b)

    def enforce(self, action):
        # Revocation terminates this simulated session; no claim of endpoint enforcement.
        attempts = 0 if self.aborted else max(1, int(round(self.behaviour['sensitive_files_accessed'] + self.behaviour['failed_logins'])))
        probability = {'ALLOW': .98, 'MONITOR': .80, 'STEP_UP_AUTH': .35, 'RESTRICT': .12, 'REVOKE': 0.}[action]
        if self.strategy == 'STEALTH_EXFILTRATION' and action in ('MONITOR', 'RESTRICT'):
            probability = min(1., probability + .12)
        successes = int(self.rng.binomial(attempts, probability))
        return {'malicious_attempts': attempts, 'successful_malicious_actions': successes,
                'exfiltrated_mb': self.behaviour['bytes_transferred_mb'] * successes / max(attempts, 1)}
