import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260

def test_browse_heavy_preserves_totals_and_funds_edible_plant():
    standard=Unified260(seed=9711,capacity_scale=.5,capacity_profile='standard')
    heavy=Unified260(seed=9711,capacity_scale=.5,capacity_profile='browse_heavy')
    assert standard.capacity_funding['mass']==heavy.capacity_funding['mass']
    assert standard.capacity_funding['energy']==heavy.capacity_funding['energy']
    t=heavy.bridge.tree
    assert heavy.host.book.mass[t.acct('plant','floodplain')]>standard.host.book.mass[standard.bridge.tree.acct('plant','floodplain')]
    assert heavy.host.book.audit()['rejections']==0

def test_double_funding_rejected():
    from funded_capacity_02145 import fund_floodplain_capacity
    import pytest
    s=Unified260(seed=9711,capacity_scale=.5,capacity_profile='browse_heavy')
    with pytest.raises(ValueError,match='already funded'):
        fund_floodplain_capacity(s.bridge.tree,scale=.5,profile='browse_heavy')
