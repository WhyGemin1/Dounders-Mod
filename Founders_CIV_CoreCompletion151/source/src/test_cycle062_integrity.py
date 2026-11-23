"""Cycle062 experimental checks: physical transfer, opt-out and drift disclosure."""
from pathlib import Path
from founders_civ.integration.compat import check
from integrated_02160 import Unified260

def test_capacity_is_finite_and_conserved():
    a=Unified260(seed=6201,capacity_scale=0)
    b=Unified260(seed=6201,capacity_scale=1)
    for field in ('mass','energy'):
        x=getattr(a.host.book,field);y=getattr(b.host.book,field)
        assert abs(sum(x.values())-sum(y.values()))<1e-7
        assert dict(x)!=dict(y)
    assert b.host.book.audit()['rejections']==0

def test_capacity_disabled_no_new_resources():
    a=Unified260(seed=6202,capacity_scale=0)
    b=Unified260(seed=6202,capacity_scale=0)
    for _ in range(3):a.step();b.step()
    assert a.report()==b.report()
    assert dict(a.host.book.energy)==dict(b.host.book.energy)

def test_baseline_drift_explicitly_recorded():
    root=Path(__file__).resolve().parents[1]/'world023024'
    if not root.exists():root=Path(__file__).resolve().parents[1].parent/'world023024'
    d=check(root,root/'docs/INTEGRATION_025/BASELINE_HASHES.json')
    assert d['status']=='drift_requires_review'
    assert 'founders_civ/experimental/world_trees.py' in d['changed_files']
    assert 'founder_world.html' in d['changed_files']
    assert len(d['changed_files']) == 2
