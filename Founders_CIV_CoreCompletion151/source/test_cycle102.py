import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES

def test_forage_priority_conservation_and_equal_funding():
    a=Unified260(seed=9711,counts={k:8 for k in SPECIES},capacity_scale=.5,capacity_profile='standard')
    b=Unified260(seed=9711,counts={k:8 for k in SPECIES},capacity_scale=.5,capacity_profile='forage_priority')
    assert a.capacity_funding['mass']==b.capacity_funding['mass']
    assert a.capacity_funding['energy']==b.capacity_funding['energy']
    assert b.host.book.mass[b.bridge.tree.acct('plant','floodplain')]>a.host.book.mass[a.bridge.tree.acct('plant','floodplain')]
    for s in (a,b):
        audit=s.host.book.audit()
        assert abs(audit['mass_error'])<1e-6 and abs(audit['energy_error'])<1e-6 and audit['rejections']==0

def test_invalid_profile_rejected():
    import pytest
    with pytest.raises(ValueError):
        Unified260(seed=9711,capacity_scale=.5,capacity_profile='unfunded_mint')
