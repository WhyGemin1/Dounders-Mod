"""Cycle039 family-pair integration tests: one economy, no guaranteed survival."""
from collections import Counter
import pytest
from unified_02136 import Unified239
from family_pair_02136 import HabitatBridge239
from habitat_bridge import SPECIES
from species_life_02115 import PROFILES


def sim(**kwargs):
    return Unified239(seed=9711,founding_families=True,**kwargs)


def total_mass(b):return sum(b.mass.values())
def total_energy(b):return sum(b.energy.values())


def test_five_species_get_four_reproductive_pairs_each():
    s=sim();bridge=s.bridge
    assert bridge.book is s.host.book is s.host.sim.book
    assert len(bridge.actors)==40 and len(bridge.family_pairs)==20
    assert Counter(x.species for x in bridge.actors.values())=={species:8 for species in SPECIES}
    for pair_id,(mom_id,dad_id) in bridge.family_pairs.items():
        mom,dad=bridge.actors[mom_id],bridge.actors[dad_id]
        assert mom.sex=='F' and dad.sex=='M'
        assert mom.stage==dad.stage=='adult'
        assert mom.habitat==dad.habitat
        assert bridge.partner(mom) is dad
        assert bridge.partner(dad) is mom
        assert mom.family_id==dad.family_id==pair_id
    assert s.host.book.audit()['rejections']==0


@pytest.mark.parametrize('bad', [
    {'ridge_hound':6}, {'field_mouse':9}, {'field_mouse':7}, {'field_mouse':0}
])
def test_underfunded_or_incomplete_family_founding_rejected(bad):
    counts={s:8 for s in SPECIES}; counts.update(bad)
    with pytest.raises(ValueError):sim(counts=counts)


def test_funded_maternal_provision_debits_plant_chemical_and_father():
    s=sim();b=s.bridge
    mother_id,father_id=next(pair for pair in b.family_pairs.values() if b.actors[pair[0]].species=='field_mouse')
    mom=b.actors[mother_id];dad=b.actors[father_id]
    plant=b.tree.acct('plant',mom.habitat)
    chem=b.tree.acct('chem',mom.habitat)
    maternal=b.physical.maternal(mom)
    maternal_energy=b.physical.maternal_energy(mom)
    father_reserve=b.physical.reserve(dad)
    before=(b.book.mass[plant],b.book.mass[maternal],b.book.energy[chem],
            b.book.energy[maternal_energy],b.book.energy[father_reserve])
    mass_before=total_mass(b.book);energy_before=total_energy(b.book)
    assert b._provision_mother(mom,dad)
    after=(b.book.mass[plant],b.book.mass[maternal],b.book.energy[chem],
           b.book.energy[maternal_energy],b.book.energy[father_reserve])
    assert after[0]<before[0] and after[1]>before[1]
    assert after[2]<before[2] and after[3]>before[3]
    assert after[4]<before[4]
    assert total_mass(b.book)==pytest.approx(mass_before,abs=1e-7)
    assert total_energy(b.book)==pytest.approx(energy_before,abs=1e-7)
    assert b.book.audit()['rejections']==0


def test_partner_redistributes_finite_energy_before_burn():
    s=sim();b=s.bridge
    fid,mid=next(iter(b.family_pairs.values()))
    mother=b.actors[fid];dad=b.actors[mid]
    receiver=b.physical.reserve(mother)
    donor=b.physical.reserve(dad)
    b.book.move(energy=[(receiver,'environment:heat',.020)])
    before_rec=b.book.energy[receiver]
    before_donor=b.book.energy[donor]
    before=total_energy(b.book)
    b._metabolize(mother)
    assert b.family_fluxes['partner_support_events']>=1
    assert b.book.energy[receiver]>before_rec-.001
    assert b.book.energy[donor]<before_donor
    assert total_energy(b.book)==pytest.approx(before,abs=1e-7)
    b.book.audit()


def test_funded_birth_assigns_both_living_caregivers():
    s=sim();b=s.bridge
    mom_id,dad_id=next(pair for pair in b.family_pairs.values() if b.actors[pair[0]].species=='ridge_hound')
    mom=b.actors[mom_id];dad=b.actors[dad_id]
    b.day=1;mom.pregnancy_father=dad.id;mom.pregnant_until=1
    assert b.book.mass[b.physical.maternal(mom)]>=PROFILES[mom.species].newborn_mass()
    old=set(b.actors);mass_before=total_mass(b.book);energy_before=total_energy(b.book)
    n=b._birth(mom)
    assert n>=1
    kids=[b.actors[x] for x in set(b.actors)-old]
    assert len(kids)==n
    assert all(x.caregiver_ids=={mom.id,dad.id} for x in kids)
    assert all(x.family_id==mom.family_id for x in kids)
    assert all(x.parent_ids==(mom.id,dad.id) for x in kids)
    assert total_mass(b.book)==pytest.approx(mass_before,abs=1e-7)
    assert total_energy(b.book)==pytest.approx(energy_before,abs=1e-7)
    b.book.audit()


def test_pair_benefits_config_is_control_without_changing_start_state():
    a=sim(family_benefits=True);b=sim(family_benefits=False)
    assert len(a.bridge.family_pairs)==len(b.bridge.family_pairs)==20
    assert a.bridge.book.mass==b.bridge.book.mass
    assert a.bridge.book.energy==b.bridge.book.energy
    assert a.bridge.rng.getstate()==b.bridge.rng.getstate()
    a.run(5);b.run(5)
    assert a.bridge.family_fluxes['provision_events']>0
    assert b.bridge.family_fluxes['provision_events']==0
    assert a.host.book.audit()['rejections']==b.host.book.audit()['rejections']==0


def test_exact_restore_same_family_energy_and_events(tmp_path):
    a=sim();a.run(10)
    path=tmp_path/'family_10.pkl';a.save(path)
    b=Unified239.load(path)
    assert b.bridge.partner_of==a.bridge.partner_of
    a.run(5);b.run(5)
    assert a.report()==b.report()
    assert a.bridge.census()==b.bridge.census()
    assert a.bridge.rng.getstate()==b.bridge.rng.getstate()
    assert a.host.book.audit()['rejections']==0


def test_default_adapter_unchanged_without_family_feature():
    s=Unified239(seed=9711,founding_families=False)
    assert not isinstance(s.bridge,HabitatBridge239)


@pytest.mark.parametrize('species', list(SPECIES))
def test_all_species_can_have_physically_funded_two_caregiver_birth(species):
    s=sim();b=s.bridge
    mom_id,dad_id=next(pair for pair in b.family_pairs.values()
                       if b.actors[pair[0]].species==species)
    mom=b.actors[mom_id];dad=b.actors[dad_id]
    p=PROFILES[species]
    # Controlled due birth checks funding for every species; not an assertion
    # that an unassisted random simulation would achieve pregnancy.
    maternal=b.physical.maternal(mom)
    deficit=max(0.,p.newborn_mass()-b.book.mass[maternal])
    if deficit:
        donor=b.tree.acct('plant',mom.habitat)
        b.physical.convert([(donor,maternal,deficit)])
    b.day=1
    mom.pregnant_until=1;mom.pregnancy_father=dad.id
    before_mass=total_mass(b.book);before_energy=total_energy(b.book)
    old=set(b.actors)
    n=b._birth(mom)
    assert n>=1
    for id in set(b.actors)-old:
        child=b.actors[id]
        assert child.caregiver_ids=={mom.id,dad.id}
        assert child.parent_ids==(mom.id,dad.id)
    assert total_mass(b.book)==pytest.approx(before_mass,abs=1e-7)
    assert total_energy(b.book)==pytest.approx(before_energy,abs=1e-7)
    b.book.audit()


def test_dead_or_absent_partner_cannot_supply_resources():
    s=sim();b=s.bridge
    mom_id,dad_id=next(iter(b.family_pairs.values()))
    mom=b.actors[mom_id];dad=b.actors[dad_id]
    b._death(dad,'age')
    assert b.partner(mom) is None
    before=total_energy(b.book)
    b._metabolize(mom)
    assert b.family_fluxes['partner_support_events']==0
    assert total_energy(b.book)==pytest.approx(before,abs=1e-7)
    b.book.audit()


def test_predator_provision_requires_carrion_not_plants():
    s=sim();b=s.bridge
    mom_id,dad_id=next(pair for pair in b.family_pairs.values()
                       if b.actors[pair[0]].species=='ridge_hound')
    mom=b.actors[mom_id];dad=b.actors[dad_id]
    source=b.carrion(mom.habitat)
    energy_source=b.physical.carrion_energy(mom.habitat)
    maternal=b.physical.maternal(mom)
    prior=b.book.mass[maternal]
    # No carrion in the initial habitat: hounds cannot provision from plants.
    assert b.book.mass[source]==0
    assert not b._provision_mother(mom,dad)
    assert b.book.mass[maternal]==prior
    # Controlled fixture: physically transfer *existing* plant material and
    # chemical energy to synthetic carcass accounts, so Book is still balanced.
    plant=b.tree.acct('plant',mom.habitat)
    chem=b.tree.acct('chem',mom.habitat)
    b.physical.convert([(plant,source,.010)])
    b.book.move(energy=[(chem,energy_source,.001)])
    mass_before=total_mass(b.book);energy_before=total_energy(b.book)
    assert b._provision_mother(mom,dad)
    assert b.book.mass[source]<.010
    assert b.book.mass[maternal]>prior
    assert total_mass(b.book)==pytest.approx(mass_before,abs=1e-7)
    assert total_energy(b.book)==pytest.approx(energy_before,abs=1e-7)
    b.book.audit()
