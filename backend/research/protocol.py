"""Shared scoring and policy implementation for comparisons and ablations."""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
from app.services.attacker_adaptation import AttackerAdaptationEngine, RESPONSES
from app.ml.game_engine import AdaptiveStackelbergGameEngine

VARIANTS = ('Baseline', '+ AAS', '+ AAS + RES', 'Full SentinelAI')


def split_chronologically(frame):
    dates = np.array(sorted(frame.date.unique()))
    if len(dates) < 10:
        raise ValueError('Need at least ten distinct dates for temporal splits')
    a, b = int(len(dates)*.6), int(len(dates)*.8)
    train = frame[frame.date < dates[a]].copy()
    valid = frame[(frame.date >= dates[a]) & (frame.date < dates[b])].copy()
    test = frame[frame.date >= dates[b]].copy()
    return train, valid, test


class ResearchModels:
    def __init__(self, features, seed=0, max_train=6000):
        self.features, self.seed, self.max_train = list(features), seed, max_train
        self.scaler = StandardScaler()
        self.iforest = IsolationForest(n_estimators=100, contamination='auto', random_state=seed, n_jobs=1)
        self.ocsvm = OneClassSVM(nu=.05, gamma='scale')

    def fit(self, train, calibration):
        benign = train[train.label.eq(0)]
        if len(benign) < 20:
            raise ValueError('Insufficient benign training rows')
        self.medians = benign[self.features].median().fillna(0.)
        self.metrics = AttackerAdaptationEngine.from_training(benign, self.features)
        # Bootstrap clean training observations: estimates training-sample variability across seeds.
        sample = benign.sample(n=min(self.max_train, len(benign)), replace=True, random_state=self.seed)
        x = self.scaler.fit_transform(sample[self.features].fillna(self.medians))
        self.iforest.fit(x)
        self.ocsvm.fit(x)
        cal = calibration[calibration.label.eq(0)]
        if len(cal) < 20:
            raise ValueError('Insufficient benign calibration rows')
        raw = self.raw_scores(cal)
        self.anchors = {}
        for key, values in raw.items():
            low, high = np.quantile(values, [.50, .99])
            self.anchors[key] = (float(low), float(max(high-low, 1e-9)))
        return self

    def raw_scores(self, frame):
        x = self.scaler.transform(frame[self.features].fillna(self.medians))
        return {'Isolation Forest': -self.iforest.decision_function(x),
                'One-Class SVM': -self.ocsvm.decision_function(x)}

    def scores(self, frame):
        raw = self.raw_scores(frame)
        normalized = [np.clip((v-self.anchors[k][0])/self.anchors[k][1], 0, 1) for k,v in raw.items()]
        raw['risk'] = 100. * np.mean(normalized, axis=0)
        return raw


def static_action(score):
    return ('ALLOW' if score < 25 else 'MONITOR' if score < 45 else
            'STEP_UP_AUTH' if score < 60 else 'RESTRICT' if score < 80 else 'REVOKE')


def decide(variant, risk, behaviour, previous, metrics):
    previous = previous or {}
    prev_action = previous.get('action', 'UNKNOWN')
    prev_features = previous.get('behaviour', {})
    aas = metrics.calculate_adaptation_score(behaviour, prev_features, prev_action)
    effectiveness = metrics.effectiveness(risk, previous.get('risk', 0.), behaviour, prev_features, prev_action)
    res = effectiveness['score']
    state = metrics.classify_state(behaviour)
    # All arms LOG the metrics. Only designated components influence their policy.
    score = risk
    if variant != 'Baseline':
        score += 20. * aas
    if variant in ('+ AAS + RES', 'Full SentinelAI') and effectiveness['available']:
        score += 15. * (1.-res) * (risk/100.)
    details = {}
    if variant == 'Full SentinelAI':
        details = AdaptiveStackelbergGameEngine(metrics).resolve_optimal_defense(
            risk, state, aas, res, prev_action, effectiveness['available'])
        action = details['selected_action']
        # Continuous game-derived detection score. Threshold calibrated on validation only.
        score = 100. * (details['urgency'] + max(0., details['expected_utility'] - details['defender_utilities']['ALLOW']))
    else:
        action = static_action(score)
    return {'action': action, 'score': score, 'aas': aas, 'res': res,
            'res_available': effectiveness['available'], 'res_components': effectiveness['components'],
            'state': state, 'previous_defence': prev_action, 'game': details}


def replay(frame, risks, variant, metrics):
    histories, scores, rows = {}, [], []
    # frame must already be sorted by date/user. Histories reset at partition boundaries.
    for record, risk in zip(frame.to_dict('records'), risks):
        user = str(record['user_id'])
        behaviour = {f: float(record[f]) for f in metrics.scales if f in record and pd.notna(record[f])}
        previous = histories.get(user)
        decision = decide(variant, float(risk), behaviour, previous, metrics)
        scores.append(decision['score'])
        rows.append({'user_id': user, 'date': record['date'], 'label': int(record['label']),
                     'risk': float(risk), 'score': decision['score'], 'action': decision['action'],
                     'previous_defence': decision['previous_defence'], 'aas': decision['aas'],
                     'res': decision['res'], 'res_available': decision['res_available'],
                     'attacker_state': decision['state']})
        histories[user] = {'behaviour': behaviour, 'risk': float(risk), 'action': decision['action']}
    return np.array(scores), rows
