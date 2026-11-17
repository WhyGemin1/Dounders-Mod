"""C018: finite, voluntary stewardship for the Realm supporting private Trees."""
import pickle
import pytest
from run_world_tree_pilot import bootstrap
from founders_civ.core.founder_parent_stewardship import (
    dependent_parent_ids, inspect_parent, propose_parent_stewardship, tend_parent)


def world():
    sim, realm, tree_id = bootstrap(seed=820)
    sim.founder_parent_stewardship_enabled = True
    return sim, realm, tree_id


def eligible_child_owner(sim, realm):
    child = next(c for c in sim.seeds.plants.values() if c['kind']=='world' and c['parent']==realm)
    return child['owner']


def reserve_low(sim, realm):
    key = f'reserve:{realm}'
    balance = sim.book.energy[key]
    if balance > .20:
        sim.book.move(energy=[(key, 'environment:heat', balance-.20)])


def test_actual_descendant_owner_has_interest_not_every_founder():
    sim, realm, tree = world()
    owner = eligible_child_owner(sim, realm)
    assert realm in dependent_parent_ids(sim, owner)
    outsider = next(x for x in sim.founders.people if x not in (owner,sim.seeds.plants[realm]['owner']))
    assert realm not in dependent_parent_ids(sim, outsider)
    assert len(sim.founders.people) == 100


def test_inspection_is_local_and_book_neutral():
    sim, realm, tree = world()
    owner=eligible_child_owner(sim,realm)
    sim.founders.people[owner].location='ridge'
    before=sim.book.seq
    with pytest.raises(ValueError,match='site'):
        inspect_parent(sim, owner, realm)
    sim.founders.people[owner].location='riverbank'
    inspect_parent(sim,owner,realm)
    assert sim.book.seq == before
    assert sim.seeds.owner_reserve_knowledge[realm][owner]['tick']==sim.tick


def test_a_real_depletion_triggers_voluntary_funded_care_and_replay():
    sim, realm, tree=world()
    owner=eligible_child_owner(sim,realm)
    sim.founders.people[owner].location='riverbank'
    reserve_low(sim,realm)
    inspect_parent(sim,owner,realm)
    options=propose_parent_stewardship(sim,owner)
    choice=next(c for c in options if c[1]=='parent_steward' and c[3][0]==realm)
    amount=choice[3][1]
    from_pool=sim.book.energy[f'founder:{owner}']
    to_pool=sim.book.energy[f'reserve:{realm}']
    seq=sim.book.seq
    transaction=tend_parent(sim,owner,choice[3],decision_id='decision-1')
    assert sim.book.seq==seq+1
    assert sim.book.energy[f'founder:{owner}']==pytest.approx(from_pool-amount)
    assert sim.book.energy[f'reserve:{realm}']==pytest.approx(to_pool+amount)
    assert sim.book.audit()['energy_error']==pytest.approx(0,abs=1e-6)
    assert tend_parent(sim,owner,choice[3],decision_id='decision-1') == transaction
    assert sim.book.seq==seq+1


def test_cannot_consume_another_founders_reserve_or_mint_energy():
    sim, realm, tree=world()
    owner=eligible_child_owner(sim,realm)
    other=next(x for x in sim.founders.people if x not in (owner,sim.seeds.plants[realm]['owner']))
    sim.founders.people[other].location='riverbank'
    before=sim.book.seq
    with pytest.raises(ValueError,match='dependent'):
        tend_parent(sim,other,(realm,.30),'decision-2')
    assert sim.book.seq==before


def test_disabled_policy_cannot_tend():
    sim,realm,tree=world()
    owner=eligible_child_owner(sim,realm)
    sim.founder_parent_stewardship_enabled=False
    assert propose_parent_stewardship(sim,owner)==[]
    with pytest.raises(ValueError,match='disabled'):
        tend_parent(sim,owner,(realm,.30),'decision-2')


def test_insufficient_existing_fuel_has_no_side_effect():
    sim,realm,tree=world()
    owner=eligible_child_owner(sim,realm)
    sim.founders.people[owner].location='riverbank'
    reserve_low(sim,realm)
    inspect_parent(sim,owner,realm)
    fuel=f'founder:{owner}'
    balance=sim.book.energy[fuel]
    if balance>.12:
        sim.book.move(energy=[(fuel,'environment:heat',balance-.12)])
    seq=sim.book.seq
    with pytest.raises(ValueError,match='insufficient'):
        tend_parent(sim,owner,(realm,.30),'decision-2')
    assert sim.book.seq==seq
    sim.book.audit()


def test_checkpoint_replay_is_exact_for_a_parent_transfer():
    sim,realm,tree=world()
    owner=eligible_child_owner(sim,realm)
    sim.founders.people[owner].location='house'
    reserve_low(sim,realm)
    inspect_parent(sim,owner,realm)
    restored=pickle.loads(pickle.dumps(sim))
    for world_sim in (sim,restored):
        tend_parent(world_sim,owner,(realm,.30),'decision-checkpoint')
    assert dict(sim.book.energy)==dict(restored.book.energy)
    assert dict(sim.book.mass)==dict(restored.book.mass)
    assert sim.book.seq==restored.book.seq
