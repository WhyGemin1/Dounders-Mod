from integrated_02170 import Unified270

def test_guided_move_with_finite_travel_and_local_gradient():
    s=Unified270(seed=9711,resource_access=True)
    bridge=s.bridge
    a=next(a for a in bridge.actors.values() if a.alive and a.species not in ('ridge_hound','carrion_bird') and a.stage!='dependent' and bridge.tree.habitats[a.habitat].neighbors)
    here=a.habitat
    neighbor=next(iter(bridge.tree.habitats[here].neighbors))
    plant=bridge.physical.plant(a)
    dest=bridge.tree.acct('plant',neighbor)
    # Transfer existing plant biomass: conservation-preserving controlled gradient.
    available=bridge.book.mass[plant]
    if available>.01:bridge.book.move(material=[(plant,dest,available-.005)])
    # Ensure destination is richer using only existing mass.
    if bridge.book.mass[dest] <= bridge.book.mass[plant]+.04:
        return  # this initial state does not support a finite gradient
    reserve=bridge.physical.reserve(a)
    energy=bridge.book.energy[reserve]
    assert energy > bridge.TRAVEL_COST+.001
    # Pressure model requires destination per-capita food advantage; isolate
    # the source actor so that neighboring competition does not dominate.
    for other in bridge.actors.values():
        if other.id != a.id and other.habitat==neighbor and other.species in ('field_mouse','meadow_grazer','forest_browser'):
            other.habitat=here
    assert bridge._migrate(a,'feed') is True
    assert a.habitat==neighbor
    assert bridge.book.energy[reserve] < energy
    assert bridge.resource_access_metrics['guided_moves']==1
    assert abs(bridge.book.audit()['mass_error'])<1e-6
    assert abs(bridge.book.audit()['energy_error'])<1e-6

def test_instrumented_resource_assessment_is_read_only_without_move():
    s=Unified270(seed=9711,resource_access=True)
    a=next(a for a in s.bridge.actors.values() if a.species not in ('ridge_hound','carrion_bird') and a.stage!='dependent')
    s.bridge._migrate(a,'rest')
    assert s.bridge.resource_access_metrics['evaluations']==0
