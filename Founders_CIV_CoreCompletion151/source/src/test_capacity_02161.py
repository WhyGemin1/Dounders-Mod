import pytest
from integrated_02160 import Unified260
from funded_capacity_02145 import fund_floodplain_capacity

def test_finite_funding_conserves_all_stocks():
    a=Unified260(seed=9911,capacity_scale=0)
    b=Unified260(seed=9911,capacity_scale=1)
    assert sum(a.host.book.mass.values())==pytest.approx(sum(b.host.book.mass.values()),abs=1e-7)
    assert sum(a.host.book.energy.values())==pytest.approx(sum(b.host.book.energy.values()),abs=1e-7)
    assert b.host.book.audit()['rejections']==0

def test_double_funding_rejected_without_mutation():
    s=Unified260(seed=9912,capacity_scale=1)
    before=(dict(s.host.book.mass),dict(s.host.book.energy))
    with pytest.raises(ValueError,match='already funded'):
        fund_floodplain_capacity(s.bridge.tree,scale=1)
    assert before==(dict(s.host.book.mass),dict(s.host.book.energy))

def test_invalid_scale_rejected_without_mutation():
    s=Unified260(seed=9913,capacity_scale=0)
    before=(dict(s.host.book.mass),dict(s.host.book.energy))
    with pytest.raises(ValueError,match='scale'):
        fund_floodplain_capacity(s.bridge.tree,scale=3)
    assert before==(dict(s.host.book.mass),dict(s.host.book.energy))
