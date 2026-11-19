"""C072: exact-decision paid-work replay against the real Core151 Book."""
from types import SimpleNamespace

import pytest

from founders_civ.core.ledger import Book
from founders_civ.core.founder_recovery import RecoveryState, paid_work


def simulation():
    book = Book()
    book.seed_energy('founder:F001', 10.)
    book.freeze()
    founder = SimpleNamespace(alive=True)
    return SimpleNamespace(
        book=book,
        founders=SimpleNamespace(people={'F001': founder}),
        recovery_states={'F001': RecoveryState()},
    )


def test_work_replay_preserves_book_fatigue_and_transaction_identity():
    sim = simulation()
    first = paid_work(sim, 'F001', 'build', 2., decision_id='decision-001')
    balance = sim.book.energy['founder:F001']
    fatigue = sim.recovery_states['F001'].fatigue
    seq = sim.book.seq
    second = paid_work(sim, 'F001', 'build', 2., decision_id='decision-001')
    assert second is first
    assert sim.book.seq == seq == 1
    assert sim.book.energy['founder:F001'] == balance
    assert sim.recovery_states['F001'].fatigue == fatigue
    assert sim.book.audit()['max_abs_energy_error'] <= 1e-7


def test_work_replay_rejects_conflicting_cost_and_missing_receipt():
    sim = simulation()
    paid_work(sim, 'F001', 'build', 1., decision_id='same')
    with pytest.raises(ValueError, match='conflicting work decision'):
        paid_work(sim, 'F001', 'build', 1.5, decision_id='same')
    sim.work_receipts.clear()
    with pytest.raises(ValueError, match='missing work replay receipt'):
        paid_work(sim, 'F001', 'build', 1., decision_id='same')
    assert sim.book.seq == 1


def test_failed_payment_and_invalid_cost_do_not_mutate_book_or_fatigue():
    sim = simulation()
    assert paid_work(sim, 'F001', 'build', 100., decision_id='too-large') is False
    for cost in (float('nan'), float('inf'), -1.):
        with pytest.raises(ValueError):
            paid_work(sim, 'F001', 'build', cost, decision_id='bad')
    sim.recovery_states['F001'].fatigue = 1.
    with pytest.raises(ValueError, match='nonfinite physical work cost'):
        paid_work(sim, 'F001', 'build', 1.5e308, decision_id='overflow')
    sim.recovery_states['F001'].fatigue = 0.
    assert sim.book.seq == 0
    assert sim.recovery_states['F001'].fatigue == 0.
    assert sim.book.energy['founder:F001'] == 10.


def test_two_distinct_work_decisions_consume_distinct_real_fuel():
    sim = simulation()
    paid_work(sim, 'F001', 'build', 1., decision_id='a')
    paid_work(sim, 'F001', 'build', 1., decision_id='b')
    assert sim.book.seq == 2
    assert sim.book.energy['environment:heat'] > 2.
    assert sim.book.energy['founder:F001'] < 8.


def test_same_decision_different_action_fails_closed_without_second_debit():
    sim = simulation()
    first = paid_work(sim, 'F001', 'build', 1., decision_id='one')
    before = (sim.book.seq, sim.book.energy['founder:F001'],
              sim.recovery_states['F001'].fatigue)
    with pytest.raises(ValueError, match='conflicting work decision action'):
        paid_work(sim, 'F001', 'harvest', 1., decision_id='one')
    assert (sim.book.seq, sim.book.energy['founder:F001'],
            sim.recovery_states['F001'].fatigue) == before
    assert paid_work(sim, 'F001', 'build', 1., decision_id='one') is first


def test_checkpoint_lost_sidecar_rejects_action_alias_replay():
    sim = simulation()
    paid_work(sim, 'F001', 'build', 1., decision_id='one')
    before = (sim.book.seq, sim.book.energy['founder:F001'],
              sim.recovery_states['F001'].fatigue)
    sim.work_receipts.clear()
    with pytest.raises(ValueError, match='conflicting work decision action'):
        paid_work(sim, 'F001', 'harvest', 1., decision_id='one')
    assert (sim.book.seq, sim.book.energy['founder:F001'],
            sim.recovery_states['F001'].fatigue) == before


def test_ambiguous_colon_identifiers_fail_before_book_mutation():
    sim = simulation()
    initial = (sim.book.seq, sim.book.energy['founder:F001'],
               sim.recovery_states['F001'].fatigue)
    for action, decision in (('build:extra', 'same'),
                             ('build', 'prefix:same'),
                             ('build:prefix', 'same')):
        with pytest.raises(ValueError, match='ambiguous work operation identity'):
            paid_work(sim, 'F001', action, 1., decision_id=decision)
    assert (sim.book.seq, sim.book.energy['founder:F001'],
            sim.recovery_states['F001'].fatigue) == initial
    assert not sim.book.operations


def test_normal_work_identity_still_replays_exactly_once():
    sim = simulation()
    first = paid_work(sim, 'F001', 'build', 1., decision_id='same')
    assert paid_work(sim, 'F001', 'build', 1., decision_id='same') is first
    assert sim.book.seq == 1
    assert sim.book.audit()['max_abs_energy_error'] <= 1e-7


def test_receipt_without_authoritative_book_operation_fails_closed():
    sim = simulation()
    paid_work(sim, 'F001', 'build', 1., decision_id='orphan')
    original = (sim.book.seq, sim.book.energy['founder:F001'],
                sim.recovery_states['F001'].fatigue)
    sim.book.operations.pop('founder:work:F001:build:orphan')
    with pytest.raises(ValueError, match='work receipt/Book checkpoint mismatch'):
        paid_work(sim, 'F001', 'build', 1., decision_id='orphan')
    assert (sim.book.seq, sim.book.energy['founder:F001'],
            sim.recovery_states['F001'].fatigue) == original


def test_receipt_with_conflicting_book_transaction_fails_closed():
    sim = simulation()
    paid_work(sim, 'F001', 'build', 1., decision_id='first')
    paid_work(sim, 'F001', 'build', 1., decision_id='second')
    key = 'founder:work:F001:build:first'
    signature, _ = sim.book.operations[key]
    sim.book.operations[key] = (signature, sim.book.operations['founder:work:F001:build:second'][1])
    before = sim.book.seq
    with pytest.raises(ValueError, match='work receipt/Book checkpoint mismatch'):
        paid_work(sim, 'F001', 'build', 1., decision_id='first')
    assert sim.book.seq == before


def test_boolean_work_cost_fails_closed_without_book_or_fatigue_mutation():
    sim = simulation()
    before = (sim.book.seq, sim.book.energy['founder:F001'],
              sim.recovery_states['F001'].fatigue)
    for cost in (True, False):
        with pytest.raises(ValueError, match='invalid work cost'):
            paid_work(sim, 'F001', 'build', cost, decision_id='bool-cost')
    assert (sim.book.seq, sim.book.energy['founder:F001'],
            sim.recovery_states['F001'].fatigue) == before
    assert not sim.book.operations


def test_whitespace_aliased_work_decision_fails_closed():
    sim = simulation()
    before = (sim.book.seq, dict(sim.book.energy), sim.recovery_states['F001'].fatigue)
    for decision in (' leading', 'trailing ', ' both ', '\tbad', 'bad\n'):
        with pytest.raises(ValueError, match='invalid work decision ID'):
            paid_work(sim, 'F001', 'build', 1., decision_id=decision)
    assert (sim.book.seq, dict(sim.book.energy), sim.recovery_states['F001'].fatigue) == before
    assert not sim.book.operations
    assert sim.book.audit()['max_abs_energy_error'] <= 1e-7


def test_whitespace_aliased_work_action_fails_closed():
    sim = simulation()
    before = (sim.book.seq, dict(sim.book.energy), sim.recovery_states['F001'].fatigue)
    for action in (' build', 'build ', ' build ', '\tbuild', 'build\n'):
        with pytest.raises(ValueError, match='invalid work action'):
            paid_work(sim, 'F001', action, 1., decision_id='same')
    assert (sim.book.seq, dict(sim.book.energy), sim.recovery_states['F001'].fatigue) == before
    assert not sim.book.operations
    assert sim.book.audit()['max_abs_energy_error'] <= 1e-7
