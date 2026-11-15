"""C015: actual WORLD-024 / SOCIAL-021 / Book food ownership to digestion integration."""
import pickle
import pytest
from run_world_tree_pilot import bootstrap
from founders_civ.core.founder_harvesting import observed_lots, perform_harvest
from founders_civ.core.founder_nutrition import propose_nutrition, perform_nutrition


def prepared():
    sim, _realm, tid = bootstrap(seed=821)
    tree = sim.world_trees.worlds[tid]
    tree.enable_provisioning()
    for _ in range(17):
        sim.step()
    person = 'F001'
    sim.founder_harvest_enabled = True
    sim.founder_nutrition_enabled = True
    sim.founders.people[person].location = 'riverbank'
    tree.observe(person)
    tree.observations[person]['known_lots'] = observed_lots(tree)
    food = next(x['lot'] for x in tree.observations[person]['known_lots'] if x['kind'] == 'food')
    return sim, tree, person, food


def harvest(sim, tree, founder, lot):
    return perform_harvest(sim, founder, (tree.id, lot, 'food'))


def test_real_world_harvest_ingest_digest_conserves_single_book():
    sim, tree, founder, lot = prepared()
    prior_energy = sim.book.energy[f'founder:{founder}']
    harvest(sim, tree, founder, lot)
    assert any(x[1] == 'food_ingest' for x in sim._proposals(founder, []))
    ingest = perform_nutrition(sim, founder, 'food_ingest', (tree.id, lot))
    assert ingest.kind == 'ingest'
    assert sim.book.energy[f'founder:{founder}'] == pytest.approx(prior_energy)
    assert sim.book.energy[f'body_chemical:founder:{founder}'] == pytest.approx(0)
    assert any(x[1] == 'food_digest' for x in sim._proposals(founder, []))
    digest = perform_nutrition(sim, founder, 'food_digest', (tree.id, lot))
    assert digest.kind == 'transform'
    assert sim.book.mass[f'assimilated:founder:{founder}'] == pytest.approx(.05)
    assert sim.book.mass[f'waste:founder:{founder}'] == pytest.approx(.03)
    assert sim.book.energy[f'body_chemical:founder:{founder}'] == pytest.approx(.015)
    audit = sim.book.audit()
    assert abs(audit['mass_error']) < 1e-5
    assert abs(audit['energy_error']) < 1e-5
    assert len(sim.founders.people) == 100
    assert len({f.id for f in sim.founders.people.values()}) == 100
    assert any(e['action'] == 'founder_food_digested' for e in sim.events)


def test_control_default_is_disabled_and_owner_cannot_be_spoofed():
    sim, tree, founder, lot = prepared()
    harvest(sim, tree, founder, lot)
    before = sim.book.seq
    assert propose_nutrition(sim, 'F002') == []
    with pytest.raises(ValueError, match='never harvested'):
        perform_nutrition(sim, 'F002', 'food_ingest', (tree.id, lot))
    sim.founder_nutrition_enabled = False
    assert propose_nutrition(sim, founder) == []
    with pytest.raises(ValueError, match='disabled'):
        perform_nutrition(sim, founder, 'food_ingest', (tree.id, lot))
    assert sim.book.seq == before


def test_digest_replay_keeps_lot_identity_and_no_new_transactions():
    sim, tree, founder, lot = prepared()
    harvest(sim, tree, founder, lot)
    perform_nutrition(sim, founder, 'food_ingest', (tree.id, lot))
    result = perform_nutrition(sim, founder, 'food_digest', (tree.id, lot))
    seq = sim.book.seq
    assert perform_nutrition(sim, founder, 'food_digest', (tree.id, lot)) == result
    assert sim.book.seq == seq
    assert propose_nutrition(sim, founder) == []


def test_checkpoint_resume_preserves_nutrition_and_idempotency():
    sim, tree, founder, lot = prepared()
    harvest(sim, tree, founder, lot)
    clone = pickle.loads(pickle.dumps(sim))
    for instance in (sim, clone):
        perform_nutrition(instance, founder, 'food_ingest', (tree.id, lot))
        perform_nutrition(instance, founder, 'food_digest', (tree.id, lot))
        assert instance.book.audit()['energy_error'] < 1e-5
    assert dict(sim.book.energy) == dict(clone.book.energy)
    assert dict(sim.book.mass) == dict(clone.book.mass)
    assert sim.book.operations == clone.book.operations
    assert [f.id for f in sim.founders.people.values()] == [f.id for f in clone.founders.people.values()]


def test_energy_empty_founder_can_eat_but_not_digest_without_existing_fuel():
    sim, tree, founder, lot = prepared()
    harvest(sim, tree, founder, lot)
    original = sim.book.energy[f'founder:{founder}']
    sim.book.move(energy=[(f'founder:{founder}', 'environment:heat', original)])
    assert any(x[1] == 'food_ingest' for x in sim._proposals(founder, []))
    perform_nutrition(sim, founder, 'food_ingest', (tree.id, lot))
    assert propose_nutrition(sim, founder) == []  # no phantom work fuel
    with pytest.raises(ValueError, match='insufficient existing metabolic fuel'):
        perform_nutrition(sim, founder, 'food_digest', (tree.id, lot))
    assert sim.book.mass[f'gut:founder:{founder}:lot:{lot}'] == pytest.approx(.08)
    sim.book.audit()


def test_scheduler_do_executes_existing_choice_and_does_not_double_ingest():
    sim, tree, founder, lot = prepared()
    harvest(sim, tree, founder, lot)
    choice = next(x for x in sim._proposals(founder, []) if x[1] == 'food_ingest')
    before = sim.book.seq
    sim._do(founder, choice, [], None, parent=None)
    assert sim.book.seq == before + 1
    assert sim.book.mass[f'gut:founder:{founder}:lot:{lot}'] == pytest.approx(.08)
    assert not any(x[1] == 'food_ingest' for x in sim._proposals(founder, []))
    choice2 = next(x for x in sim._proposals(founder, []) if x[1] == 'food_digest')
    sim._do(founder, choice2, [], None, parent=None)
    assert sim.book.mass[f'assimilated:founder:{founder}'] == pytest.approx(.05)
    sim.book.audit()
