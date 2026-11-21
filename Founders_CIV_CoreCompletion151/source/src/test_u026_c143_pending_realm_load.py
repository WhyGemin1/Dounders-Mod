"""U026-C143 regression: pending autonomous World proposals distribute realm choice."""
from types import SimpleNamespace
from founders_civ.core.founder_tree_agency import _realm_to_develop


def _sim(blueprints=()):
    plants = {
        'realm-a': {'id': 'realm-a', 'kind': 'realm', 'status': 'stable'},
        'realm-b': {'id': 'realm-b', 'kind': 'realm', 'status': 'stable'},
    }
    return SimpleNamespace(seeds=SimpleNamespace(
        plants=plants,
        blueprints={str(i): SimpleNamespace(kind='world', parent_id=parent, stage=stage)
                    for i, (parent, stage) in enumerate(blueprints)}))


def test_pending_world_blueprint_counts_toward_parent_load():
    assert _realm_to_develop(_sim()) == 'realm-a'
    assert _realm_to_develop(_sim([('realm-a', 'draft')])) == 'realm-b'
    assert _realm_to_develop(_sim([('realm-a', 'researching')])) == 'realm-b'
    assert _realm_to_develop(_sim([('realm-a', 'validated')])) == 'realm-b'


def test_planted_and_non_world_blueprints_not_double_counted():
    sim = _sim([('realm-a', 'planted')])
    assert _realm_to_develop(sim) == 'realm-a'
    sim.seeds.blueprints['other'] = SimpleNamespace(
        kind='realm', parent_id='realm-a', stage='draft')
    assert _realm_to_develop(sim) == 'realm-a'


def test_parent_selection_is_independent_of_blueprint_iteration_order():
    a = _sim([('realm-a', 'draft'), ('realm-b', 'draft')])
    b = _sim([('realm-b', 'draft'), ('realm-a', 'draft')])
    assert _realm_to_develop(a) == _realm_to_develop(b) == 'realm-a'
