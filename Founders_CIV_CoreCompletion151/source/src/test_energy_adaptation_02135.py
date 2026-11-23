"""Cycle038 focused tests: energy cannot be minted by fasting, rest or fat."""
import pytest
from unified_02135 import Unified238
from energy_adaptation_02135 import HabitatBridge238, PREDATOR_FASTING_DAYS


def sim(seed=9711, **kw):
    return Unified238(seed=seed,digestion=True,predator_scavenging=True,
                      mate_search=True,predator_energy_adaptation=True,**kw)

def hound(s):
    return next(a for a in s.bridge.actors.values() if a.alive and a.species=='ridge_hound')

def energy_total(book):
    return sum(book.energy.values())


def test_opt_in_control_and_requires_book():
    control=Unified238(seed=9711,digestion=True)
    assert not isinstance(control.bridge,HabitatBridge238)
    with pytest.raises(ValueError): Unified238(predator_energy_adaptation=True)
    s=sim()
    assert s.bridge.book is s.host.book is s.host.sim.book
    s.host.book.audit()


def test_fat_from_funded_meal_surplus():
    s=sim();b=s.bridge;a=hound(s)
    source=b.tree.acct('chem',a.habitat)
    reserve=b.physical.reserve(a)
    before=energy_total(b.book)
    old=b.book.energy[reserve]
    b.book.move(energy=[(source,reserve,.012)])
    stored=b._store_fat(a,old)
    assert stored>0
    assert b.book.energy[b.fat_account(a)]==pytest.approx(stored)
    assert energy_total(b.book)==pytest.approx(before,abs=1e-7)
    assert b.book.audit()['rejections']==0


def test_rest_mobilizes_funded_storage_and_reduces_burn():
    s1=sim();s2=sim()
    a1=hound(s1);a2=hound(s2)
    for s,a in ((s1,a1),(s2,a2)):
        b=s.bridge; source=b.tree.acct('chem',a.habitat)
        b.book.move(energy=[(source,b.fat_account(a),.009)])
        reserve=b.physical.reserve(a)
        b.book.move(energy=[(reserve,'environment:heat',.019)])
    s1.bridge.needs_last[a1.id]='rest'
    s2.bridge.needs_last[a2.id]='search'
    total_before=energy_total(s1.bridge.book)
    r1=s1.bridge.book.energy[s1.bridge.physical.reserve(a1)]
    r2=s2.bridge.book.energy[s2.bridge.physical.reserve(a2)]
    s1.bridge._metabolize(a1)
    s2.bridge._metabolize(a2)
    assert s1.bridge.book.energy[s1.bridge.physical.reserve(a1)]>r1
    assert s2.bridge.book.energy[s2.bridge.physical.reserve(a2)]<r2
    assert s1.bridge.predator_energy_fluxes['rest_days']==1
    assert s1.bridge.book.energy[s1.bridge.fat_account(a1)]<.009
    assert energy_total(s1.bridge.book)==pytest.approx(total_before,abs=1e-7)
    s1.bridge.book.audit()


def test_starvation_grace_finite_and_no_free_fuel():
    s=sim();b=s.bridge;a=hound(s)
    source=b.physical.reserve(a)
    e=b.book.energy[source]
    b.book.move(energy=[(source,'environment:heat',e)])
    a.condition=.8
    b.fasting_days[a.id]=1
    b._death(a,'starvation')
    assert a.alive
    assert b.book.energy[source]==0
    b.fasting_days[a.id]=PREDATOR_FASTING_DAYS
    b._death(a,'starvation')
    assert not a.alive
    b._check_registry();b.book.audit()


def test_fat_follows_carcass_on_real_death():
    s=sim();b=s.bridge;a=hound(s)
    chem=b.tree.acct('chem',a.habitat)
    b.book.move(energy=[(chem,b.fat_account(a),.005)])
    carrion=b.physical.carrion_energy(a.habitat)
    old=b.book.energy[carrion]
    b._death(a,'age')
    assert not a.alive
    assert b.book.energy[b.fat_account(a)]==0
    assert b.book.energy[carrion]>=old+.005-1e-9
    b.book.audit()


def test_food_urgency_beats_idle_action():
    s=sim();b=s.bridge;a=hound(s)
    reserve=b.physical.reserve(a)
    excess=max(0.,b.book.energy[reserve]-.003)
    if excess:b.book.move(energy=[(reserve,'environment:heat',excess)])
    b.day=41
    choice,_,_=b.evaluate_needs(a)
    assert choice in ('feed','search')
    assert b.needs_last[a.id]==choice


def test_exact_checkpoint_resume(tmp_path):
    a=sim();a.run(5)
    path=tmp_path/'recover.pkl';a.save(path)
    b=Unified238.load(path)
    a.run(7);b.run(7)
    assert a.report()==b.report()
    assert a.host.book.audit()['rejections']==0
    assert a.host.book is a.bridge.book


def test_courtship_funded_and_not_guaranteed():
    s=sim();b=s.bridge
    pair=[x for x in b.actors.values() if x.alive and x.species=='ridge_hound'][:2]
    if len(pair)<2:pytest.skip('initial hounds did not fund')
    mother,father=pair
    mother.sex='F';father.sex='M'
    for a in pair:a.age=200;a.condition=1.
    if father.habitat!=mother.habitat:
        reserve=b.physical.reserve(father)
        b.book.move(energy=[(reserve,'environment:heat',b.TRAVEL_COST)])
        father.habitat=mother.habitat
    p=__import__('species_life_02115').PROFILES['ridge_hound']
    maternal=b.physical.maternal(mother)
    missing=max(0.,p.birth_cost*.1-b.book.mass[maternal])
    if missing:
        b.physical.convert([(b.physical.plant(mother),maternal,missing)])
    live=b.physical.live(mother)
    missing_body=max(0.,p.adult_mass()*.70-b.book.mass[live])
    if missing_body:b.physical.convert([(b.physical.plant(mother),live,missing_body)])
    reserve=b.physical.reserve(mother)
    if b.book.energy[reserve]<.015:
        b.book.move(energy=[(b.physical.chem(mother),reserve,.016-b.book.energy[reserve])])
    b.day=50
    choice,_,_=b.evaluate_needs(mother)
    assert choice=='mate'
    before=b.book.energy[reserve]
    b._reproduce()
    assert b.predator_energy_fluxes['courtship_attempts']==1
    assert b.book.energy[reserve] <= before-0.00015+1e-10
    b.book.audit()
