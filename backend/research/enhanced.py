"""Validation-selected preprocessing. No test rows enter fit or selection.

Common representation selected for all models/policies by mean validation AP of
IF and OCSVM. This uses validation labels and is reported as such. User reference
statistics are fitted on benign training rows only and frozen thereafter.
"""
import numpy as np
from scipy.special import expit
from sklearn.metrics import average_precision_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from research.protocol import ResearchModels
from app.services.attacker_adaptation import AttackerAdaptationEngine


class EnhancedResearchModels(ResearchModels):
    def _matrix(self, frame, mode):
        raw = frame[self.features].fillna(self.medians).to_numpy(dtype=float)
        if mode == 'raw':
            return raw
        logged = np.log1p(np.maximum(raw, 0))
        if mode == 'log1p':
            return logged
        references = self.user_reference.reindex(frame.user_id.astype(str)).fillna(self.global_reference).to_numpy()
        # Directional deviations preserve increases/decreases. Unknown users use population reference.
        deviation = logged - references
        return np.concatenate([logged, deviation], axis=1)

    def fit(self, train, calibration):
        benign = train[train.label.eq(0)]
        cal_benign = calibration[calibration.label.eq(0)]
        if len(benign) < 20 or len(cal_benign) < 20 or calibration.label.nunique() != 2:
            raise ValueError('Enhanced selection requires benign training/calibration and both validation classes')
        self.medians = benign[self.features].median().fillna(0.)
        self.metrics = AttackerAdaptationEngine.from_training(benign, self.features)
        logged = np.log1p(benign[self.features].fillna(self.medians).clip(lower=0))
        self.global_reference = logged.median()
        self.user_reference = logged.assign(user_id=benign.user_id.astype(str)).groupby('user_id').median()
        sample = benign.sample(n=min(self.max_train,len(benign)),replace=True,random_state=self.seed)
        self.selection = []
        candidates = []
        for mode in ('raw', 'log1p', 'personalized_log1p'):
            scaler = StandardScaler()
            x = scaler.fit_transform(self._matrix(sample, mode))
            xv = scaler.transform(self._matrix(calibration, mode))
            forest = IsolationForest(n_estimators=100,contamination='auto',random_state=self.seed,n_jobs=1).fit(x)
            svm = OneClassSVM(nu=.05,gamma='scale').fit(x)
            ap_if = average_precision_score(calibration.label, -forest.decision_function(xv))
            ap_oc = average_precision_score(calibration.label, -svm.decision_function(xv))
            score = (ap_if + ap_oc) / 2
            self.selection.append({'seed':self.seed, 'representation':mode, 'validation_if_ap':ap_if,
                                   'validation_ocsvm_ap':ap_oc, 'selection_score':score})
            candidates.append((score, mode, scaler, forest, svm))
        _, self.mode, self.scaler, self.iforest, self.ocsvm = max(candidates, key=lambda c:c[0])
        for row in self.selection:
            row['selected'] = row['representation'] == self.mode
        self.anchors = {}
        for key, values in self.raw_scores(cal_benign).items():
            low, high = np.quantile(values, [.50,.99])
            self.anchors[key] = (float(low),float(max(high-low,1e-9)))
        return self

    def raw_scores(self, frame):
        x = self.scaler.transform(self._matrix(frame, self.mode))
        return {'Isolation Forest':-self.iforest.decision_function(x),
                'One-Class SVM':-self.ocsvm.decision_function(x)}

    def scores(self, frame):
        raw = self.raw_scores(frame)
        # Smooth mapping avoids collapsing the entire top 1% into an identical risk.
        normalized = [expit(4*((v-self.anchors[k][0])/self.anchors[k][1]-.5)) for k,v in raw.items()]
        raw['risk'] = 100*np.mean(normalized, axis=0)
        return raw


def validation_threshold(labels, scores, max_fpr=.05):
    """Maximize validation F1 under an FPR ceiling; deterministic strict-> threshold.

    Evaluate all unique score cutoffs in O(n log n), including predict-none.
    Ties favor fewer alerts. Labels come only from the validation partition.
    """
    y, s = np.asarray(labels,dtype=int), np.asarray(scores,dtype=float)
    if not np.isfinite(s).all() or len(s) != len(y) or not len(y):
        raise ValueError('Need aligned finite validation scores')
    order = np.argsort(-s,kind='stable'); s, y = s[order], y[order]
    ends = np.flatnonzero(np.r_[s[:-1] != s[1:], True])
    tp = np.cumsum(y)[ends]; fp = ends+1-tp
    positives, negatives = y.sum(),len(y)-y.sum()
    f1 = 2*tp/np.maximum(2*tp+fp+positives-tp,1)
    allowed = fp/max(negatives,1) <= max_fpr
    quality = np.where(allowed,f1,-1)
    if quality.max(initial=0) <= 0:
        return float(s.max())
    i = int(np.argmax(quality))
    return float(np.nextafter(s[ends[i]], -np.inf))
