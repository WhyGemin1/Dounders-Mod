import pytest
from spatial_map_02137 import Unified240

def test_map_is_deterministic_and_preserves_book():
    a=Unified240(seed=9711); b=Unified240(seed=9711)
    assert a.bridge.positions==b.bridge.positions
    assert a.host.book.audit()==b.host.book.audit()
    assert len(a.bridge.actors)==40

def test_invalid_map_size():
    with pytest.raises(ValueError):Unified240(grid_size=1)

def test_spatial_census_has_generation_and_no_fabricated_g2():
    a=Unified240(); c=a.bridge.spatial_census()
    assert c['living']==40
    assert not c['second_generation_reproduced']
    assert all(0<=x<a.bridge.grid_size and 0<=y<a.bridge.grid_size for _,x,y in a.bridge.positions.values())
