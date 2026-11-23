from integrated_02192 import Unified292

def test_opt_in_and_conservation():
    s=Unified292(seed=9711,reproductive_ecology=True,capacity_scale=.5,edible_budget=1)
    p=s.edible_policy;t=s.bridge.tree;b=t.book
    p.reference=1000.
    before=b.audit();donor=b.mass['plant:Solara:grassland'];food=b.mass['forage:browse:floodplain']
    result=p.act(t)
    assert result['funded']
    assert abs(b.mass['plant:Solara:grassland']-donor+.25)<1e-9
    assert abs(b.mass['forage:browse:floodplain']-food-.25)<1e-9
    assert abs(b.audit()['mass_error']-before['mass_error'])<1e-6
    assert abs(b.audit()['energy_error']-before['energy_error'])<1e-6
    assert not p.act(t)['funded']

def test_no_funding_when_budget_zero():
    s=Unified292(seed=9711,reproductive_ecology=True,capacity_scale=.5,edible_budget=0)
    s.edible_policy.reference=1000.
    assert s.edible_policy.act(s.bridge.tree)['reason']=='budget_exhausted'
