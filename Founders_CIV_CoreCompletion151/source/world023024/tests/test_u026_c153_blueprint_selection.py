"""U026-C153: deterministic active World blueprint ownership selection."""
from types import SimpleNamespace
from founders_civ.core.founder_tree_agency import _own_blueprint

def _sim(*blueprints):
    return SimpleNamespace(seeds=SimpleNamespace(
        blueprints={b.id: b for b in blueprints}))

def _b(id, author='F001', stage='draft', kind='world'):
    return SimpleNamespace(id=id, author=author, stage=stage, kind=kind)

def test_active_blueprint_selection_is_insertion_independent():
    a, b = _b('a', stage='validated'), _b('b')
    assert _own_blueprint(_sim(a, b), 'F001').id == 'a'
    assert _own_blueprint(_sim(b, a), 'F001').id == 'a'

def test_terminal_and_other_founder_blueprints_are_ignored():
    assert _own_blueprint(_sim(_b('a', stage='failed'), _b('b')), 'F001').id == 'b'
    assert _own_blueprint(_sim(_b('a', author='F002'), _b('b')), 'F001').id == 'b'

def test_no_active_blueprint_returns_none():
    assert _own_blueprint(_sim(_b('a', stage='abandoned')), 'F001') is None
