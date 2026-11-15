from integrated_02189 import Unified289
from capacity_renewal_02189 import renew_floodplain
import pytest

def test_finite_renewal():
    s=Unified289(seed=9711,capacity_scale=.5)
    b=s.host.book; before=b.audit(); donor=b.mass['plant:Solara:grassland']; target=b.mass[s.bridge.tree.acct('plant','floodplain')]
    out=renew_floodplain(s.bridge.tree,.5)
    assert out['funded']
    assert b.mass['plant:Solara:grassland']==pytest.approx(donor-.125)
    assert b.mass[s.bridge.tree.acct('plant','floodplain')]==pytest.approx(target+.25)
    assert b.audit()['mass_error']==pytest.approx(before['mass_error'],abs=1e-6)
    assert b.audit()['energy_error']==pytest.approx(before['energy_error'],abs=1e-6)

def test_invalid_no_mutation():
    s=Unified289(seed=9711)
    b=s.host.book; before=(dict(b.mass),dict(b.energy))
    with pytest.raises(ValueError):renew_floodplain(s.bridge.tree,2)
    assert before==(dict(b.mass),dict(b.energy))

def test_disabled_no_renewal():
    s=Unified289(seed=9711,renewal_scale=0)
    assert s.renewals==[]
