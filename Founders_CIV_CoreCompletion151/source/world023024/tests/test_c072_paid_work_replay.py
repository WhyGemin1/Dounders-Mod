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
        paid_work(sim, 'F001', 'build', 1e308, decision_id='overflow')
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
