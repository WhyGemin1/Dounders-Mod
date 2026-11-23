"""Opt-in controlled starting cohort fixture; no energy or mass creation."""
from species_life_02115 import PROFILES, MASS_SCALE

def prepare_hound_pair(bridge, *, maternal_fraction=1.0, adjacent=True):
    """Make existing animals eligible, funding maternal stock from local plant biomass.

    Does not spawn animals, add resources, or modify predator success.
    Age/sex/condition are explicitly stipulated initial conditions.
    Raises if local biomass or travel energy cannot fund the fixture.
    """
    if not 0 <= maternal_fraction <= 1:
        raise ValueError('maternal_fraction must be within [0,1]')
    hounds=[a for a in bridge.actors.values() if a.alive and a.species=='ridge_hound']
    female=next((a for a in hounds if a.sex=='F'),None)
    male=next((a for a in hounds if a.sex=='M'),None)
    if female is None or male is None:
        raise ValueError('requires existing opposite-sex hounds')
    p=PROFILES['ridge_hound']
    target=p.birth_cost*MASS_SCALE*maternal_fraction
    maternal=bridge.physical.maternal(female)
    delta=max(0,target-bridge.book.mass[maternal])
    plant=bridge.physical.plant(female)
    if bridge.book.mass[plant]+1e-10<delta:
        raise ValueError('insufficient local plant biomass; no free maternal stock')
    neighbors=tuple(sorted(bridge.tree.habitats[female.habitat].neighbors))
    if adjacent and not neighbors:
        raise ValueError('no adjacent habitat')
    destination=neighbors[0] if adjacent else female.habitat
    travel=bridge.TRAVEL_COST if male.habitat!=destination else 0
    if bridge.book.energy[bridge.physical.reserve(male)]<travel+.0005:
        raise ValueError('insufficient travel energy')
    before_mass=sum(bridge.book.mass.values())
    before_energy=sum(bridge.book.energy.values())
    if delta:
        bridge.physical.convert([(plant,maternal,delta)])
    if travel:
        bridge.book.move(energy=[(bridge.physical.reserve(male),'environment:heat',travel)])
    female.age=male.age=p.maturity+1
    female.condition=male.condition=1.0
    male.habitat=destination
    assert abs(sum(bridge.book.mass.values())-before_mass)<1e-8
    assert abs(sum(bridge.book.energy.values())-before_energy)<1e-8
    return {'female':female.id,'male':male.id,'maternal_transfer':delta,'travel_energy':travel,'adjacent':adjacent}
