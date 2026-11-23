from integrated_02187 import Unified287

def test_growth_opt_in():
    s=Unified287(seed=9711,growth_allocation=True)
    assert s.bridge.growth_allocation
    assert s.bridge.__class__.__name__=='ReproductiveBridge287'

def test_control():
    s=Unified287(seed=9711,growth_allocation=False)
    assert not s.bridge.growth_allocation
