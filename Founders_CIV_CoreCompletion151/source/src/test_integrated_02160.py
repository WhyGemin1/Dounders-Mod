import pickle
import pytest
from integrated_02160 import Unified260

def test_integrated_runtime_finite_capacity_and_one_book():
    base=Unified260(seed=9711,capacity_scale=0)
    sim=Unified260(seed=9711,capacity_scale=1)
    assert sim.host.book is sim.bridge.tree.book
    assert sim.host.sim.ecology.book is sim.host.book
    assert sim.host.book.mass['plant:Solara:grassland'] == pytest.approx(base.host.book.mass['plant:Solara:grassland']-2.5)
    assert sim.host.book.energy['house'] == pytest.approx(base.host.book.energy['house']-.5)
    assert sum(sim.host.book.mass.values()) == pytest.approx(sum(base.host.book.mass.values()))
    assert sum(sim.host.book.energy.values()) == pytest.approx(sum(base.host.book.energy.values()))
    assert sim.host.book.audit()['rejections']==0
    assert len(sim.host.sim.founders.people)==100

def test_opt_out_capacity_matches_old_engine():
    from unified_02142 import Unified242
    old=Unified242(seed=9712,five_habitats=True,family_benefits=True,resource_aware_family=True)
    new=Unified260(seed=9712,capacity_scale=0)
    for _ in range(3):old.step();new.step()
    assert old.bridge.events==new.bridge.events
    assert dict(old.host.book.mass)==dict(new.host.book.mass)
    assert dict(old.host.book.energy)==dict(new.host.book.energy)

def test_checkpoint_integrated_exact_replay():
    a=Unified260(seed=9713,capacity_scale=1)
    for _ in range(3):a.step()
    b=pickle.loads(pickle.dumps(a,pickle.HIGHEST_PROTOCOL))
    for _ in range(3):a.step();b.step()
    assert a.report()==b.report()
    assert a.bridge.events==b.bridge.events

def test_invalid_capacity_without_fifth():
    with pytest.raises(ValueError):Unified260(five_habitats=False,capacity_scale=1)
