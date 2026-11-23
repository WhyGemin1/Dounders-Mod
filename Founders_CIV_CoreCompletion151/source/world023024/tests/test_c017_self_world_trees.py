"""C017: physically funded, individually owned autonomous World Tree Creation."""
import pickle
import pytest
from run_world_tree_pilot import bootstrap
from founders_civ.core.founder_tree_agency import propose_self_trees, fund_own_tree
from founders_civ.core.founder_harvesting import observed_lots, perform_harvest


def setup_world():
    sim, realm, tid = bootstrap(seed=820)
    tree = sim.world_trees.worlds[tid]
    tree.enable_provisioning()
    for _ in range(17):
        sim.step()
    sim.founder_tree_independence_enabled = True
    sim.founder_harvest_enabled = True
    return sim, realm, tid


def validated_blueprint(sim, owner, realm):
    sim.founders.people[owner].location = 'riverbank'
    b = sim.seeds.draft(owner, 'world', 'Food Tree of ' + owner, realm, x=63, y=43)
    sim.seeds.research(owner, b.id)
    sim.step()
    if sim.tick not in b.research_ticks:
        sim.seeds.research(owner, b.id)
    reviewer = 'F007' if owner != 'F007' else 'F008'
    sim.founders.people[reviewer].location = 'riverbank'
    sim.seeds.validate(reviewer, b.id)
    return b


def harvest_a_fruit(sim, tid, owner):
    tree = sim.world_trees.worlds[tid]
    sim.founders.people[owner].location = 'riverbank'
    tree.observe(owner)
    tree.observations[owner]['known_lots'] = observed_lots(tree)
    lot = next(x['lot'] for x in tree.observations[owner]['known_lots'] if x['kind'] == 'fruit')
    perform_harvest(sim, owner, (tid, lot, 'fruit'))
    return lot


def test_founder_proposes_an_independent_tree_not_food_for_all():
    sim, realm, tid = setup_world()
    # No new Tree agenda unless this Founder owns finite propagation fruit.
    assert propose_self_trees(sim, 'F002', []) == []
    harvest_a_fruit(sim, tid, 'F002')
    own = propose_self_trees(sim, 'F002', [])
    assert any(x[1] == 'seed_design' and x[3] == ('world', realm) for x in own)
    assert 'F002' != sim.world_trees.worlds[tid].owner
    assert len(sim.founders.people) == 100
    assert len(sim.world_trees.worlds) >= 1
    sim.book.audit()


def test_fruit_required_before_plant_and_no_partial_changes():
    sim, realm, tid = setup_world()
    b = validated_blueprint(sim, 'F002', realm)
    before = sim.book.seq
    mass = dict(sim.book.mass)
    with pytest.raises(ValueError, match='funded Creation fruit'):
        sim.seeds.plant('F002', b.id)
    assert sim.book.seq == before
    assert dict(sim.book.mass) == mass
    assert len(sim.world_trees.worlds) >= 1


def test_owned_fruit_funds_second_world_tree_without_minting():
    sim, realm, tid = setup_world()
    b = validated_blueprint(sim, 'F002', realm)
    lot = harvest_a_fruit(sim, tid, 'F002')
    plans = propose_self_trees(sim, 'F002', [])
    assert any(p[1] == 'seed_fund' and p[3] == (b.id, tid, lot) for p in plans)
    tx = fund_own_tree(sim, 'F002', (b.id, tid, lot))
    seq = sim.book.seq
    assert fund_own_tree(sim, 'F002', (b.id, tid, lot)) == tx
    assert sim.book.seq == seq
    assert sim.book.mass[f'world_seed:{b.id}'] == pytest.approx(.10)
    assert sim.book.energy[f'ce:seed:{b.id}'] == pytest.approx(1.)
    # A second Founder voluntarily transfers already-owned physical fuel,
    # rather than minting energy for the new creator.
    sim.book.move(energy=[('founder:F003', 'founder:F002', 1.5)])
    tree = sim.seeds.plant('F002', b.id)
    assert tree['kind'] == 'world' and tree['owner'] == 'F002'
    assert tree['id'] != tid
    assert sim.world_trees.worlds[tree['id']].provisioning is not None
    assert sim.book.mass[f'world_seed:planted:{tree["id"]}'] == pytest.approx(.10)
    assert sim.book.energy[f'ce:world:{tree["id"]}'] == pytest.approx(1.)
    assert sim.book.energy[f'ce:seed:{b.id}'] == pytest.approx(0.)
    assert sim.book.mass[f'world_seed:{b.id}'] == pytest.approx(0.)
    assert propose_self_trees(sim, 'F002', []) == []
    assert len(sim.founders.people) == 100
    assert len({f.id for f in sim.founders.people.values()}) == 100
    assert sim.book.audit()['mass_error'] < 1e-6
    assert sim.book.audit()['energy_error'] < 1e-6


def test_other_founder_cannot_steal_fruit_to_create_own_tree():
    sim, realm, tid = setup_world()
    b = validated_blueprint(sim, 'F002', realm)
    lot = harvest_a_fruit(sim, tid, 'F003')
    before = sim.book.seq
    with pytest.raises(ValueError, match='does not own'):
        fund_own_tree(sim, 'F002', (b.id, tid, lot))
    assert sim.book.seq == before
    assert not any(x[1] == 'seed_fund' for x in propose_self_trees(sim, 'F002', []))


def test_creation_checkpoint_replay_exact():
    sim, realm, tid = setup_world()
    b = validated_blueprint(sim, 'F002', realm)
    lot = harvest_a_fruit(sim, tid, 'F002')
    copy = pickle.loads(pickle.dumps(sim))
    for world in (sim, copy):
        fund_own_tree(world, 'F002', (b.id, tid, lot))
        world.book.move(energy=[('founder:F003', 'founder:F002', 1.5)])
        world.seeds.plant('F002', b.id)
        world.book.audit()
    assert sim.seeds.export() == copy.seeds.export()
    assert dict(sim.book.mass) == dict(copy.book.mass)
    assert dict(sim.book.energy) == dict(copy.book.energy)
    assert sim.book.operations == copy.book.operations
    assert [f.id for f in sim.founders.people.values()] == [f.id for f in copy.founders.people.values()]


def test_control_only_preserves_old_unfruit_funded_planting():
    sim, realm, tid = setup_world()
    sim.founder_tree_independence_enabled = False
    b = validated_blueprint(sim, 'F002', realm)
    assert sim.seeds.plant('F002', b.id)['kind'] == 'world'


def test_no_blueprint_flood_without_personally_harvested_fruit():
    sim, realm, tid = setup_world()
    initial = len(sim.seeds.blueprints)
    # The Tree's fruit is finite. Knowledge or ownership cannot be inferred
    # merely because another actor's Tree exists.
    for founder in ('F002','F003','F004','F005'):
        assert propose_self_trees(sim, founder, []) == []
    assert len(sim.seeds.blueprints) == initial
    assert propose_self_trees(sim, 'F001', []) == []  # active realm caretaker


def test_peer_review_replaces_endless_research_after_two_cycles():
    sim, realm, tid = setup_world()
    harvest_a_fruit(sim, tid, 'F002')
    b = sim.seeds.draft('F002','world','Voluntary food Tree',realm)
    sim.seeds.research('F002',b.id)
    sim.step()
    if sim.tick not in b.research_ticks:
        sim.seeds.research('F002',b.id)
    # Two real research observations suffice. Repeating observations forever
    # would consume fuel without making a fruit-funded Tree more feasible.
    assert len(b.research_ticks)>=2
    choices = propose_self_trees(sim,'F002',[])
    assert not any(p[1]=='seed_research' for p in choices)
    all_choices = sim._proposals('F002',[])
    assert not any(p[1]=='seed_research' and p[3]==b.id for p in all_choices)


def test_scheduler_funds_personal_world_seed_once():
    sim,realm,tid=setup_world()
    b=validated_blueprint(sim,'F002',realm)
    lot=harvest_a_fruit(sim,tid,'F002')
    option=next(p for p in sim._proposals('F002',[]) if p[1]=='seed_fund')
    count_before=sim.counter['founder_own_tree_seed_funded']
    result=sim._do('F002',option,[],None,parent='direct-test')
    assert result.kind=='transform'
    assert sim.counter['founder_own_tree_seed_funded']==count_before+1
    seq=sim.book.seq
    sim._do('F002',option,[],None,parent='direct-test')
    assert sim.book.seq==seq
    assert sim.counter['founder_own_tree_seed_funded']==count_before+1
    assert sim.book.energy[f'ce:seed:{b.id}']==pytest.approx(1.)
    sim.book.audit()


def test_g2_existing_tree_owner_may_expand_only_after_acquiring_real_fruit():
    """A Founder owning one WORLD-024 Tree may fund another; no global one-Tree cap.

    The existing world is a REAL seeded Tree, and the new propagation lot
    is transferred through the authoritative Book, not fabricated in a test.
    """
    sim, realm, tid = setup_world()
    owner = sim.seeds.plants[tid]['owner']
    assert sim.seeds.plants[tid]['status'] == 'stable'
    assert sim.world_trees.worlds[tid].owner == owner
    before = (dict(sim.book.mass), dict(sim.book.energy), sim.book.seq)
    # Without personally acquired propagation fruit, repeat-Tree creation
    # remains unavailable even to an established Tree owner.
    assert not any(p[1] == 'seed_design' for p in propose_self_trees(sim, owner, []))
    assert before == (dict(sim.book.mass), dict(sim.book.energy), sim.book.seq)

    lot = harvest_a_fruit(sim, tid, owner)
    assert sim.book.mass[f'fruit:lot:{lot}:founder:{owner}'] > 0
    assert sim.book.energy[f'ce:fruit:lot:{lot}:founder:{owner}'] > 0
    # A proposal can require existing work fuel, which is transferred rather
    # than minted when this established Founder has spent their reserve.
    if sim.book.energy.get(f'founder:{owner}', 0) < .08:
        donor = max((f for f in sim.founders.people if f != owner),
                    key=lambda f: sim.book.energy.get(f'founder:{f}', 0))
        needed = .09 - sim.book.energy.get(f'founder:{owner}', 0)
        sim.book.move(energy=[(f'founder:{donor}', f'founder:{owner}', needed)])
    pre_proposal = (dict(sim.book.mass), dict(sim.book.energy), sim.book.seq)
    choices = propose_self_trees(sim, owner, [])
    assert any(p[1] == 'seed_design' and p[3] == ('world', realm) for p in choices)
    assert pre_proposal == (dict(sim.book.mass), dict(sim.book.energy), sim.book.seq)
    assert len(sim.founders.people) == 100
    assert len({person.id for person in sim.founders.people.values()}) == 100
    assert abs(sim.book.audit()['mass_error']) < 1e-5
    assert abs(sim.book.audit()['energy_error']) < 1e-5


def test_realm_owner_with_real_fruit_can_propose_first_personal_world():
    sim, realm, tid = setup_world()
    owner = sim.seeds.plants[realm]['owner']
    assert sim.seeds.plants[realm]['kind'] == 'realm'
    assert not any(p['kind'] == 'world' and p['owner'] == owner and p['status'] == 'stable'
                   for p in sim.seeds.plants.values())
    assert propose_self_trees(sim, owner, []) == []
    harvest_a_fruit(sim, tid, owner)
    proposals = propose_self_trees(sim, owner, [])
    assert any(p[1] == 'seed_design' and p[3] == ('world', realm) for p in proposals)
    assert len(sim.founders.people) == 100
    assert sim.book.audit()['energy_error'] < 1e-6


def test_c138_tree_proposals_never_use_epsilon_fuel_overdraft(monkeypatch):
    """A near-funded voluntary design is not an executable funded proposal."""
    from types import SimpleNamespace
    import founders_civ.core.founder_tree_agency as agency
    monkeypatch.setattr(agency, '_own_fruit', lambda sim, founder: iter([('T1', 'fruit1')]))
    person = SimpleNamespace(alive=True, location='riverbank')
    sim = SimpleNamespace(
        founder_tree_independence_enabled=True,
        founders=SimpleNamespace(people={'F002': person}),
        seeds=SimpleNamespace(blueprints={}, plants={'R1': {
            'kind': 'realm', 'status': 'stable', 'id': 'R1'}}),
        book=SimpleNamespace(energy={'founder:F002': .08 - 5e-11}),
    )
    # Voluntary design is free; no fuel debit is permitted for planning.
    before = sim.book.energy['founder:F002']
    assert any(p[1] == 'seed_design' for p in agency.propose_self_trees(sim, 'F002', []))
    assert sim.book.energy['founder:F002'] == before
    sim.book.energy['founder:F002'] = 0.0
    assert any(p[1] == 'seed_design' for p in agency.propose_self_trees(sim, 'F002', []))
    assert sim.book.energy['founder:F002'] == 0.0


def test_c140_review_selects_funded_peer_regardless_of_contact_order():
    """An unfunded first peer cannot block a funded, colocated reviewer."""
    from types import SimpleNamespace
    owner = SimpleNamespace(alive=True, location='riverbank')
    weak = SimpleNamespace(alive=True, location='riverbank')
    funded = SimpleNamespace(alive=True, location='riverbank')
    blueprint = SimpleNamespace(id='B1', author='F002', kind='world',
                                parent_id='R1', stage='researching',
                                research_ticks={1, 2})
    sim = SimpleNamespace(
        founder_tree_independence_enabled=True, tick=3,
        founders=SimpleNamespace(people={'F002': owner, 'F003': weak, 'F004': funded}),
        seeds=SimpleNamespace(blueprints={'B1': blueprint},
                              plants={'R1': {'kind': 'realm', 'status': 'stable'}}),
        book=SimpleNamespace(energy={'founder:F002': 1., 'founder:F003': .10,
                                     'founder:F004': .11}))
    expected = [(5.1, 'seed_request_review', 'F004', 'B1')]
    assert propose_self_trees(sim, 'F002', ['F003', 'F004']) == expected
    assert propose_self_trees(sim, 'F002', ['F004', 'F003', 'F004']) == expected
    sim.book.energy['founder:F004'] = .11 - 5e-11
    assert propose_self_trees(sim, 'F002', ['F003', 'F004']) == []


def test_c157_fruit_selection_is_checkpoint_order_independent(monkeypatch):
    """Equivalent Book-owned inventories must select the same real fruit lot."""
    from types import SimpleNamespace
    import founders_civ.core.founder_exchange as exchange
    from founders_civ.core.founder_tree_agency import _own_fruit
    lots = ['fruit-z', 'fruit-a', 'fruit-m']
    monkeypatch.setattr(exchange, 'owned_lots', lambda sim, founder, kind: iter(lots))
    monkeypatch.setattr(exchange, '_origin', lambda sim, kind, lot: ('T1', object()))
    sim = SimpleNamespace()
    first = list(_own_fruit(sim, 'F002'))
    lots.reverse()
    second = list(_own_fruit(sim, 'F002'))
    assert first == second == [('T1', 'fruit-a'), ('T1', 'fruit-m'), ('T1', 'fruit-z')]
