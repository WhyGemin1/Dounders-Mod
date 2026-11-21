import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from juvenile_dispatch_021111 import enable_juvenile_conservation

def test_active_runtime_dispatch_and_finite_energy():
    s=Unified260(seed=9711,counts={k:8 for k in SPECIES},capacity_scale=.5,family_benefits=True,resource_aware_family=True)
    b=s.bridge
    assert b._metabolize.__func__.__module__=='family_pair_02136'
    a=next(iter(b.actors.values()))
    a.parent='synthetic-parent-for-isolated-dispatch-test';a.age=20
    reserve=b.physical.reserve(a)
    start=b.book.energy[reserve]
    enable_juvenile_conservation(b)
    b._metabolize(a)
    actual=start-b.book.energy[reserve]
    expected=min(start,.001*(.5+.5*__import__('species_life_02115').PROFILES[a.species].metabolism/.1)*.65)
    assert abs(actual-expected)<1e-10
    assert b.book.audit()['rejections']==0

def test_invalid_multiplier_rejected():
    s=Unified260(seed=9711,counts={k:8 for k in SPECIES})
    import pytest
    with pytest.raises(ValueError):enable_juvenile_conservation(s.bridge,0)

def test_family_support_preserved_during_juvenile_metabolism():
    from family_pair_02136 import PARTNER_RESERVE_FLOOR
    s=Unified260(seed=9711,counts={k:8 for k in SPECIES},family_benefits=True)
    b=s.bridge
    pair=next(((a,b.actors[pid]) for a in b.actors.values() for pid in [b.partner_of.get(a.id)] if pid in b.actors and b.partner(a) is not None),None)
    assert pair is not None
    child,donor=pair
    child.parent='test-parent';child.age=20
    ck=b.physical.reserve(child);dk=b.physical.reserve(donor)
    # Book-funded redistribution, no mint: use available energy of the donor.
    if b.book.energy[dk] <= PARTNER_RESERVE_FLOOR+.002:
        import pytest
        pytest.skip('pair donor reserve insufficient for support test')
    amount=min(.005,b.book.energy[dk]-PARTNER_RESERVE_FLOOR-.001)
    b.book.move(energy=[(ck,'environment:heat',max(0.,b.book.energy[ck]-.001))])
    enable_juvenile_conservation(b)
    before=b.family_fluxes['partner_support_events']
    b._metabolize(child)
    assert b.family_fluxes['partner_support_events']>before
    assert b.book.audit()['rejections']==0
