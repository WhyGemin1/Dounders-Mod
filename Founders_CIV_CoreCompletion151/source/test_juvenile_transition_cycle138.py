from experiment_cycle136 import make_sim
from juvenile_transition_cycle138 import enable_transition_support,JuvenileTransitionBridge138,JUVENILE_EMERGENCY_RESERVE
from juvenile_support_cycle136 import JuvenileSupportBridge136,ASSIST_CHILD_RESERVE_TARGET

def test_opt_in_preserves_baseline_and_single_book():
    baseline,_=make_sim(9711,False)
    trial,_=make_sim(9711,False)
    enable_transition_support(trial)
    assert not isinstance(baseline.bridge,JuvenileSupportBridge136)
    assert isinstance(trial.bridge,JuvenileTransitionBridge138)
    assert trial.bridge.book is trial.host.book

def test_emergency_threshold_stricter_than_dependent_target():
    assert 0 < JUVENILE_EMERGENCY_RESERVE < ASSIST_CHILD_RESERVE_TARGET

def test_no_mint_and_live_path():
    trial,_=make_sim(9711,False)
    enable_transition_support(trial)
    for _ in range(120):trial.step()
    assert trial.host.book.audit()['rejections']==0
    assert trial.bridge.juvenile_support_metrics['successful_meals']>0
