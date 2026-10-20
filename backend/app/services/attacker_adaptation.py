"""Observed response metrics. No iteration counter or ground-truth label is used."""
import math
import numpy as np

DEFAULT_SCALES = {
    'login_hour': 12., 'files_accessed': 100., 'sensitive_files_accessed': 20.,
    'bytes_transferred_mb': 1500., 'failed_logins': 5., 'privilege_level': 2.,
    'session_duration_min': 480., 'external_emails': 20., 'device_events': 10.,
    'http_events': 500., 'off_hours_events': 50.,
}
# Every completed defender decision is a conditioning event, including ALLOW.
RESPONSES = {'ALLOW', 'MONITOR', 'STEP_UP_AUTH', 'RESTRICT', 'REVOKE'}


def finite(value):
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


class AttackerAdaptationEngine:
    def __init__(self, scales=None):
        self.scales = dict(DEFAULT_SCALES if scales is None else scales)
        if not self.scales or any(not finite(v) or v <= 0 for v in self.scales.values()):
            raise ValueError('Behavioural scales must be finite and positive')

    @classmethod
    def from_training(cls, frame, features):
        """Robust ranges fitted ONLY on training data; constant features use unit range."""
        scales = {}
        for name in features:
            values = frame[name].dropna()
            if len(values):
                scales[name] = 12. if name == 'login_hour' else max(float(values.quantile(.95) - values.quantile(.05)), 1.)
        return cls(scales)

    def calculate_adaptation_score(self, current_features, prev_features, prev_action):
        if not prev_features or prev_action not in RESPONSES:
            return 0.
        distances = []
        for name, scale in self.scales.items():
            if finite(current_features.get(name)) and finite(prev_features.get(name)):
                delta = abs(float(current_features[name]) - float(prev_features[name]))
                if name == 'login_hour':
                    delta %= 24.
                    delta = min(delta, 24. - delta)
                distances.append(min(delta / scale, 1.) ** 2)
        return float(np.sqrt(np.mean(distances))) if distances else 0.

    def _index(self, features, names):
        parts = [min(max(float(features[n]), 0.) / self.scales[n], 1.)
                 for n in names if n in self.scales and finite(features.get(n))]
        return float(np.mean(parts)) if parts else None

    def activity_index(self, features):
        # Observable activity intensity, NOT a ground-truth maliciousness classifier.
        return self._index(features, ('files_accessed', 'failed_logins', 'off_hours_events', 'device_events'))

    def confidentiality_index(self, features):
        return self._index(features, ('sensitive_files_accessed', 'bytes_transferred_mb', 'external_emails'))

    def effectiveness(self, current_risk, previous_risk, current, previous, previous_defence):
        result = {'score': 0., 'available': False, 'components': {}}
        if not previous or previous_defence not in RESPONSES:
            return result
        pairs = {
            'risk_reduction': (previous_risk, current_risk, .5),
            'activity_reduction': (self.activity_index(previous), self.activity_index(current), .2),
            'confidentiality_reduction': (self.confidentiality_index(previous), self.confidentiality_index(current), .3),
        }
        weighted, total = 0., 0.
        for name, (before, after, weight) in pairs.items():
            if not finite(before) or not finite(after) or float(before) <= 0:
                continue
            reduction = float(np.clip((float(before) - float(after)) / float(before), 0., 1.))
            result['components'][name] = reduction
            weighted += weight * reduction
            total += weight
        result['available'] = total > 0
        result['score'] = weighted / total if total else 0.
        return result

    def calculate_effectiveness_score(self, current_risk, prev_risk, prev_action,
                                      current_features=None, prev_features=None):
        return self.effectiveness(current_risk, prev_risk, current_features or {},
                                  prev_features or {}, prev_action)['score']

    def classify_state(self, features):
        def val(key):
            return float(features[key]) if finite(features.get(key)) else 0.
        if val('failed_logins') >= 3:
            return 'PROBING'
        exposure = self.confidentiality_index(features) or 0.
        if exposure >= .45:
            return 'AGGRESSIVE_EXFILTRATION'
        if val('sensitive_files_accessed') > 0 or val('external_emails') > 0 or val('bytes_transferred_mb') > self.scales.get('bytes_transferred_mb', 1500.) * .02:
            return 'STEALTH_EXFILTRATION'
        return 'ROUTINE'


adaptation_engine = AttackerAdaptationEngine()
