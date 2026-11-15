import pytest
from integrated_02178 import Unified278

def test_opt_in_and_single_book():
    s=Unified278(seed=9711,unified_behavior=True,capacity_scale=.2)
    assert s.bridge.book is s.host.book
    assert s.capacity_funding['mass']>0
    assert abs(s.host.book.audit()['mass_error'])<1e-6
    assert abs(s.host.book.audit()['energy_error'])<1e-6

def test_finite_funding_debit_and_no_double_fund():
    s=Unified278(seed=9711,capacity_scale=.2)
    assert s.capacity_funding['energy']>0
    with pytest.raises(ValueError):
        from funded_capacity_02145 import fund_floodplain_capacity
        fund_floodplain_capacity(s.bridge.tree,scale=.2)

def test_behavior_finite_travel():
    s=Unified278(seed=9711,unified_behavior=True)
    b=s.bridge
    a=next(x for x in b.actors.values() if x.alive and x.species=='field_mouse' and x.stage!='dependent')
    before=s.host.book.audit()
    for _ in range(3):s.step()
    after=s.host.book.audit()
    assert abs(after['mass_error'])<1e-6
    assert abs(after['energy_error'])<1e-6
    assert after['transactions']>before['transactions']
