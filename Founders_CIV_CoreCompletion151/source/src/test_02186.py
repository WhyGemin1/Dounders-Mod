from integrated_02186 import Unified286

def test_opt_in():
    a=Unified286(seed=9711,maturation_feeding=True,reproductive_ecology=True)
    assert a.bridge.maturation_feeding
    assert a.bridge.__class__.__name__=='ReproductiveBridge286'

def test_default_off():
    a=Unified286(seed=9711,maturation_feeding=False)
    assert not a.bridge.maturation_feeding
