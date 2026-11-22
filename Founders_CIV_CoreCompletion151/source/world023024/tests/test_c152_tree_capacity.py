"""C152 regression: collapsed creations must release bounded proposal capacity."""
from types import SimpleNamespace
from founders_civ.core import founder_tree_agency as agency


def _sim(stable=0, collapsed=0, pending=0, terminal=0):
    plants = {'realm': dict(kind='realm', status='stable', id='realm', owner='none')}
    for i in range(stable):
        plants[f'live{i}'] = dict(kind='world', status='stable', id=f'live{i}', parent='realm', owner='other')
    for i in range(collapsed):
        plants[f'dead{i}'] = dict(kind='world', status='collapsed', id=f'dead{i}', parent='realm', owner='other')
    blueprints = {}
    for i in range(pending):
        blueprints[f'pending{i}'] = SimpleNamespace(stage='draft', kind='world', parent_id='realm', author='other')
    for i in range(terminal):
        blueprints[f'terminal{i}'] = SimpleNamespace(stage='failed', kind='world', parent_id='realm', author='other')
    return SimpleNamespace(
        founder_tree_independence_enabled=True,
        founders=SimpleNamespace(people={'F001': SimpleNamespace(alive=True)}),
        seeds=SimpleNamespace(plants=plants, blueprints=blueprints),
        book=SimpleNamespace(energy={'founder:F001': 1.0}),
    )


def test_collapsed_worlds_release_capacity(monkeypatch):
    monkeypatch.setattr(agency, '_own_fruit', lambda sim, founder: iter([('TREE', 'FRUIT')]))
    sim = _sim(collapsed=120, terminal=200)
    assert agency.propose_self_trees(sim, 'F001', []) == [(4.35, 'seed_design', None, ('world', 'realm'))]


def test_active_worlds_and_pending_proposals_still_fill_capacity(monkeypatch):
    monkeypatch.setattr(agency, '_own_fruit', lambda sim, founder: iter([('TREE', 'FRUIT')]))
    assert agency.propose_self_trees(_sim(stable=105), 'F001', []) == []
    assert agency.propose_self_trees(_sim(pending=105), 'F001', []) == []


def test_capacity_boundary_and_free_choice_do_not_mutate_book(monkeypatch):
    monkeypatch.setattr(agency, '_own_fruit', lambda sim, founder: iter([('TREE', 'FRUIT')]))
    sim = _sim(stable=104, collapsed=30)
    before = dict(sim.book.energy)
    assert agency.propose_self_trees(sim, 'F001', [])
    assert sim.book.energy == before
