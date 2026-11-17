"""C017 executable integration tests: physical perception, agency and Book invariants."""
import pickle
import pytest
from run_world_tree_pilot import bootstrap
from founders_civ.core.community_foraging import (propose_community_scan,
    perform_community_scan, prioritize_food)
from founders_civ.core.founder_harvesting import perform_harvest


def prepared():
    sim, _realm, tid = bootstrap(seed=820)
    sim.world_trees.worlds[tid].enable_provisioning()
    for _ in range(17): sim.step()
    sim.founder_harvest_enabled=True
    sim.founder_community_foraging_enabled=True
    return sim, tid


def test_non_owner_at_riverbank_can_see_then_harvest_identified_lot():
    sim, tid = prepared()
    observer = next(f for f in sim.founders.people if f != sim.world_trees.worlds[tid].owner)
    sim.founders.people[observer].location='riverbank'
    options=propose_community_scan(sim,observer)
    assert len(options)==1 and options[0][3]==tid
    before=dict(sim.book.mass),dict(sim.book.energy),sim.book.seq
    perform_community_scan(sim,observer,tid)
    assert (dict(sim.book.mass),dict(sim.book.energy),sim.book.seq)==before
    entries=sim.world_trees.worlds[tid].observations[observer]['known_lots']
    food=next(e['lot'] for e in entries if e['kind']=='food')
    txn=perform_harvest(sim,observer,(tid,food,'food'))
    assert txn and sim.book.mass[f'portable_food:lot:{food}:founder:{observer}']==pytest.approx(.08)
    assert abs(sim.book.audit()['mass_error']) < 1e-8  # Book audit's floating-point tolerance
    assert abs(sim.book.audit()["energy_error"]) < 1e-5


def test_no_remote_omniscient_scan_or_disabled_bypass():
    sim,tid=prepared()
    f='F052';sim.founders.people[f].location='house'
    assert propose_community_scan(sim,f)==[]
    with pytest.raises(ValueError,match='physically'):
        perform_community_scan(sim,f,tid)
    sim.founders.people[f].location='riverbank'
    sim.founder_community_foraging_enabled=False
    assert propose_community_scan(sim,f)==[]
    with pytest.raises(ValueError,match='disabled'):
        perform_community_scan(sim,f,tid)
    assert not sim.world_trees.worlds[tid].observations.get(f)


def test_stale_observation_requires_reinspection_and_does_not_reveal_balances():
    sim,tid=prepared();f='F052';sim.founders.people[f].location='riverbank'
    perform_community_scan(sim,f,tid)
    assert propose_community_scan(sim,f)==[]
    sim.tick += 7
    assert propose_community_scan(sim,f)
    sim.tick -= 7
    assert 'maintenance_reserve' not in sim.world_trees.worlds[tid].observations[f]


def test_fuel_aware_priorities_do_not_bypass_harvest_authorization():
    sim,tid=prepared();f='F052';sim.founders.people[f].location='riverbank'
    proposals=[(2.,'tree_harvest',None,(tid,'not-observed','food')),
               (2.1,'tree_harvest',None,(tid,'not-observed','fruit')),
               (2.2,'study',None,None)]
    ranked=prioritize_food(sim,f,proposals)
    assert ranked[0][0]>proposals[0][0]
    assert ranked[1][0]==proposals[1][0]
    with pytest.raises(ValueError,match='known|recent'):
        perform_harvest(sim,f,(tid,'not-observed','food'))


def test_social_scheduler_selects_local_inspection_without_resource_mint():
    sim,tid=prepared();f='F052';sim.founders.people[f].location='riverbank'
    props=sim._proposals(f,[])
    choices=[p for p in props if p[1]=='food_scan']
    assert len(choices)==1
    before=sim.book.audit(),sim.book.seq
    result=sim._do(f,choices[0],[],None,'choice-c017')
    assert result and sim.book.seq==before[1] and sim.book.audit()==before[0]
    assert len(sim.founders.people)==100


def test_checkpoint_replay_inspection_and_harvest_book_identical():
    sim,tid=prepared();f='F052';sim.founders.people[f].location='riverbank'
    clone=pickle.loads(pickle.dumps(sim))
    for world in (sim,clone):
        perform_community_scan(world,f,tid)
        lot=next(x['lot'] for x in world.world_trees.worlds[tid].observations[f]['known_lots'] if x['kind']=='food')
        perform_harvest(world,f,(tid,lot,'food'))
    assert sim.book.operations==clone.book.operations
    assert sim.book.audit()==clone.book.audit()
    assert sim.world_trees.worlds[tid].observations[f]==clone.world_trees.worlds[tid].observations[f]


def test_g2_food_only_owner_observation_does_not_crash_or_invent_census():
    """G2 seed 9711 exposed owner food scans lacking a population field.

    Missing animal census must not be interpreted as zero population and
    policy proposals must preserve the single authoritative Book.
    """
    sim, _realm, tid = bootstrap(seed=9711)
    tree = sim.world_trees.worlds[tid]
    owner = tree.owner
    sim.founders.people[owner].location = 'riverbank'
    tree.observations[owner] = {'seen_tick': sim.tick - 5, 'known_lots': []}
    if sim.book.energy[f'founder:{owner}'] < .19:
        donor = max((f for f in sim.founders.people if f != owner),
                    key=lambda f: sim.book.energy.get(f'founder:{f}', 0))
        amount = .21 - sim.book.energy[f'founder:{owner}']
        sim.book.move(energy=[(f'founder:{donor}', f'founder:{owner}', amount)])
    before = (dict(sim.book.mass), dict(sim.book.energy), sim.book.seq)
    plans = sim._proposals(owner, [])
    assert any(p[1] == 'tree_observe' and p[3] == tid for p in plans)
    assert (dict(sim.book.mass), dict(sim.book.energy), sim.book.seq) == before
    assert len(sim.founders.people) == 100
    sim.book.audit()
