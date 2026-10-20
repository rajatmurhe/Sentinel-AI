import numpy as np
import pandas as pd
from research.enhanced import validation_threshold, EnhancedResearchModels
from app.services.attacker_adaptation import AttackerAdaptationEngine
from app.ml.adaptive_attacker import AdaptiveAttacker
from app.ml.game_engine import AdaptiveStackelbergGameEngine


def test_threshold_matches_brute_force_with_ties():
    rng = np.random.default_rng(43)
    y = rng.integers(0,2,100); scores = rng.integers(0,10,100).astype(float)
    threshold = validation_threshold(y,scores,.2)
    def measure(t):
        pred = scores > t; tp = (pred & (y==1)).sum(); fp = (pred & (y==0)).sum()
        return 2*tp/max(pred.sum()+y.sum(),1) if fp/(y==0).sum() <= .2 else -1
    candidates = [scores.max()] + [np.nextafter(v,-np.inf) for v in np.unique(scores)]
    assert np.isclose(measure(threshold),max(map(measure,candidates)))


def test_aas_is_behavioural_and_res_handles_missing_history():
    metrics = AttackerAdaptationEngine({'login_hour':12.,'files_accessed':100.})
    before = {'login_hour':23., 'files_accessed':10.}
    after = {'login_hour':1., 'files_accessed':10.}
    assert metrics.calculate_adaptation_score(before,before,'ALLOW') == 0
    assert np.isclose(metrics.calculate_adaptation_score(after,before,'ALLOW'),np.sqrt(((2/12)**2)/2))
    assert not metrics.effectiveness(5,10,after,{},'UNKNOWN')['available']
    assert metrics.effectiveness(5,10,after,before,'RESTRICT')['score'] > 0


def test_attacker_depends_on_defence_and_game_uses_history():
    a,b = AdaptiveAttacker(2),AdaptiveAttacker(2)
    allowed = a.observe_and_adapt('ALLOW'); restricted = b.observe_and_adapt('RESTRICT')
    assert allowed['bytes_transferred_mb'] > restricted['bytes_transferred_mb']
    game = AdaptiveStackelbergGameEngine()
    actions = set()
    for risk in (15,30,45,60):
        low = game.resolve_optimal_defense(risk,'STEALTH_EXFILTRATION',0,1,'MONITOR')
        high = game.resolve_optimal_defense(risk,'STEALTH_EXFILTRATION',1,0,'MONITOR')
        assert high['urgency'] > low['urgency']
        actions.add((low['selected_action'],high['selected_action']))
    assert any(a != b for a,b in actions)


def test_personal_reference_is_frozen_on_training_only():
    # A validation user's extreme value cannot alter its training reference.
    frame = pd.DataFrame({'user_id':['u']*80, 'files_accessed':np.tile([1.,2.,3.,4.],20), 'label':[0]*80})
    validation = pd.DataFrame({'user_id':['u']*30,'files_accessed':[2.]*25+[100.]*5,'label':[0]*25+[1]*5})
    model = EnhancedResearchModels(['files_accessed'],0,60).fit(frame,validation)
    reference = model.user_reference.copy(deep=True)
    model.scores(validation.assign(files_accessed=1e9))
    pd.testing.assert_frame_equal(reference,model.user_reference)
    assert np.isclose(reference.loc['u','files_accessed'],np.median(np.log1p(frame.files_accessed)))
