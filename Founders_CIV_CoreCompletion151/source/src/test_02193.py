from integrated_02193 import Unified293

def test_scheduled_funding_conserves_book():
    s=Unified293(seed=9711,reproductive_ecology=True,capacity_scale=.5,edible_budget=1,scheduled_funding=True)
    before=s.host.book.audit()
    for _ in range(30):s.step()
    assert s.edible_events[-1]['funded'] is True
    assert s.edible_policy.remaining==0
    after=s.host.book.audit()
    assert abs(after['mass_error']-before['mass_error'])<1e-6
    assert abs(after['energy_error']-before['energy_error'])<1e-6

def test_control_never_spends_budget():
    s=Unified293(seed=9711,reproductive_ecology=True,capacity_scale=.5,edible_budget=0,scheduled_funding=True)
    for _ in range(30):s.step()
    assert not s.edible_events[-1]['funded']
    assert s.edible_events[-1]['reason']=='budget_exhausted'
