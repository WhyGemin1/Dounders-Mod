from integrated_02177 import Unified277

def test_opt_in_does_not_change_physical_outcome():
    a=Unified277(seed=9711,mortality_audit=False)
    b=Unified277(seed=9711,mortality_audit=True)
    for _ in range(3):a.step();b.step()
    assert a.host.book.audit()==b.host.book.audit()
    assert a.bridge.census()==b.bridge.census()
    assert b.report()['mortality_audit']['enabled']

def test_audit_tracks_feeding_without_mint():
    s=Unified277(seed=9712,mortality_audit=True)
    for _ in range(3):s.step()
    m=s.report()['mortality_audit']
    assert m.get('feeding_attempts',0)>=m.get('feeding_successes',0)
    assert m.get('energy_gained_micro',0)>=0
    assert s.host.book.audit()['mass_error']<1e-5
