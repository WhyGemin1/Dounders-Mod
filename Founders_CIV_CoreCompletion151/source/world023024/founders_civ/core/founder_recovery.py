"""U026-C016 opt-in rest and chemical-fuel mobilization for real Founders.

Energy remains exclusively on the authoritative Book. Rest never transfers
finite river CE or mints chemical fuel. Fatigue is an embodied efficiency
modifier, *not* a stock of energy and never a time/action permission token.
"""
from dataclasses import dataclass
from math import isfinite


@dataclass
class RecoveryState:
    fatigue: float = 0.0
    rest_decisions: int = 0


def state_for(sim, founder):
    if founder not in sim.founders.people:
        raise ValueError('unknown Founder')
    if not sim.founders.people[founder].alive:
        raise ValueError('active Founder required')
    return sim.recovery_states[founder]


def paid_work(sim, founder, action, base_cost, decision_id=None):
    """Fund real work from embodied fuel, with optional exact-decision replay.

    A decision identity prevents repeated physical fuel debits and fatigue
    accumulation when the same work acknowledgement is delivered twice.
    Legacy callers without a decision ID retain their previous behavior.
    """
    if isinstance(base_cost, bool) or not isinstance(base_cost, (int, float)) or not isfinite(base_cost) or base_cost < 0:
        raise ValueError('invalid work cost')
    state = state_for(sim, founder)
    # Corrupt checkpoint fatigue must not turn work into a negative fuel debit.
    if (isinstance(state.fatigue, bool) or not isinstance(state.fatigue, (int, float))
            or not isfinite(state.fatigue) or not 0. <= state.fatigue <= 1.):
        raise ValueError('invalid Founder fatigue')
    if decision_id is not None:
        if (not isinstance(decision_id, str) or not 1 <= len(decision_id) <= 72
                or decision_id != decision_id.strip()):
            raise ValueError('invalid work decision ID')
        if (not isinstance(action, str) or not 1 <= len(action) <= 40
                or action != action.strip()):
            raise ValueError('invalid work action')
        # Colon is the Book operation field separator. Reject ambiguous IDs
        # before any transfer, so action aliases cannot disguise a replay.
        if ':' in action or ':' in decision_id or ':' in founder:
            raise ValueError('ambiguous work operation identity')
        operation = f'founder:work:{founder}:{action}:{decision_id}'
        if len(operation) > 128:
            raise ValueError('work operation ID too long')
        # A replay must match its original action and requested physical cost,
        # even if fatigue has changed since the original debit.
        # Inspect replay sidecars without creating state for a rejected work
        # proposal. A failed fuel check must leave checkpoint state untouched.
        receipts = getattr(sim, 'work_receipts', None)
        if receipts is None:
            receipts = {}
        # A decision identity is unique to a Founder, not to an action name.
        # Otherwise a retried decision with a different action can spend twice.
        prefix = f'founder:work:{founder}:'
        for prior_operation in receipts:
            if (prior_operation.startswith(prefix)
                    and prior_operation.rsplit(':', 1)[-1] == decision_id
                    and prior_operation != operation):
                raise ValueError('conflicting work decision action')
        if operation in receipts:
            original_cost, txn = receipts[operation]
            if original_cost != base_cost:
                raise ValueError('conflicting work decision replay')
            # A sidecar receipt alone is not authoritative. A partially
            # restored checkpoint must not acknowledge work whose Book debit
            # is absent or whose transaction identity has changed.
            recorded = sim.book.operations.get(operation)
            if recorded is None or recorded[1] != txn:
                raise ValueError('work receipt/Book checkpoint mismatch')
            return recorded[1]
        # Book operations remain authoritative across checkpoint boundaries:
        # a lost sidecar receipt must not permit a second debit under a
        # different action name for the same Founder decision.
        for prior_operation in sim.book.operations:
            if (prior_operation.startswith(prefix)
                    and prior_operation.rsplit(':', 1)[-1] == decision_id
                    and prior_operation != operation):
                raise ValueError('conflicting work decision action')
        # Fail closed on a restored Book whose sidecar receipt was lost:
        # a second fatigue update would diverge from the original checkpoint.
        if operation in sim.book.operations:
            raise ValueError('missing work replay receipt; restore checkpoint')
    else:
        operation = None
    cost = base_cost * (1.0 + 0.6 * state.fatigue)
    if not isfinite(cost):
        raise ValueError('nonfinite physical work cost')
    account = f'founder:{founder}'
    available = sim.book.energy[account]
    # Fail closed on corrupted authoritative fuel before any work debit.
    if (isinstance(available, bool) or not isinstance(available, (int, float))
            or not isfinite(available) or available < 0):
        raise ValueError('invalid Founder work fuel')
    # The destination is authoritative too: a damaged heat account must not
    # turn a legitimate work debit into an invalid conservation transaction.
    heat_balance = sim.book.energy.get('environment:heat', 0.)
    if (isinstance(heat_balance, bool) or not isinstance(heat_balance, (int, float))
            or not isfinite(heat_balance) or heat_balance < 0):
        raise ValueError('invalid work heat destination')
    # No epsilon overdraft: the Book must never fund work from fuel that
    # does not physically exist, even when the shortfall is very small.
    if available < cost:
        return False
    if cost <= 0:
        return None
    txn = sim.book.move(energy=[(account, 'environment:heat', cost)],
                        operation_id=operation)
    state.fatigue = min(1., state.fatigue + 0.03 + 0.16 * cost)
    if operation is not None:
        if getattr(sim, 'work_receipts', None) is None:
            sim.work_receipts = {}
        sim.work_receipts[operation] = (base_cost, txn)
    return txn


def propose_rest(sim, founder):
    # Disabled recovery must not enter autonomous action selection.
    # Keep this read-only: policy toggles never spend or mint Book energy.
    if not getattr(sim, 'founder_recovery_enabled', False):
        return []
    person = sim.founders.people.get(founder)
    if person is None or not person.alive:
        return []
    state = state_for(sim, founder)
    # Never rank a proposal from a corrupt or nonfinite checkpoint state.
    # This is a read-only policy decision: no Book energy is created or spent.
    if (isinstance(state.fatigue, bool) or not isinstance(state.fatigue, (int, float))
            or not isfinite(state.fatigue) or not 0. <= state.fatigue <= 1.):
        raise ValueError('invalid Founder fatigue')
    # A restored decision counter is part of the Founder's replay identity.
    # Do not offer an autonomous rest action from a corrupt checkpoint.
    if (isinstance(state.rest_decisions, bool) or not isinstance(state.rest_decisions, int)
            or state.rest_decisions < 0):
        raise ValueError('invalid recovery decision counter')
    usable = sim.book.energy[f'founder:{founder}']
    stored = sim.book.energy.get(f'body_chemical:founder:{founder}', 0.)
    # Invalid checkpoint accounts must not influence autonomous priorities.
    # Proposal evaluation is read-only and cannot repair authoritative fuel.
    for value in (usable, stored):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
            raise ValueError('invalid Founder proposal fuel')
    # Avoid repeatedly selecting a no-op rest: with no fatigue and no
    # mobilizable stored fuel, the action cannot improve physical state.
    # Rest remains freely available whenever fatigue exists, even unfunded.
    if state.fatigue == 0. and stored < .001 - 1e-9:
        return []
    score = .03 + 1.25 * state.fatigue
    if stored >= .001 - 1e-9 and usable < .7:
        score += 3.5
    return [(score, 'rest', None, None)]


def perform_rest(sim, founder, parent=None, decision_id=None):
    if not getattr(sim, 'founder_recovery_enabled', False):
        raise ValueError('recovery policy disabled')
    person = sim.founders.people.get(founder)
    if person is None or not person.alive:
        raise ValueError('active Founder required')
    state = state_for(sim, founder)
    # A corrupt checkpoint must not turn rest into nonfinite fatigue recovery.
    if (isinstance(state.fatigue, bool) or not isinstance(state.fatigue, (int, float))
            or not isfinite(state.fatigue) or not 0. <= state.fatigue <= 1.):
        raise ValueError('invalid Founder fatigue')
    # The checkpoint counter is an identity-bearing recovery record, not a
    # quantity that may be repaired implicitly during replay.
    if (isinstance(state.rest_decisions, bool) or not isinstance(state.rest_decisions, int)
            or state.rest_decisions < 0):
        raise ValueError('invalid recovery decision counter')
    # Rest is a chosen physical action, not a purchase of elapsed time.
    # Replay identity comes from the exact decision, NOT the simulation tick.
    if decision_id is None:
        decision_id = parent if parent is not None else f'manual-{sim.next_event + 1}'
    if (not isinstance(decision_id, str) or not 1 <= len(decision_id) <= 72
            or decision_id != decision_id.strip() or ':' in decision_id):
        raise ValueError('invalid recovery decision ID')
    if not isinstance(founder, str) or ':' in founder:
        raise ValueError('ambiguous recovery Founder identity')
    operation = f'founder:rest:{founder}:{decision_id}'
    if len(operation) > 128:
        raise ValueError('recovery operation ID too long')
    if operation in sim.recovery_receipts:
        # A receipt is not proof that the authoritative Book survived restore.
        # New funded rests record their exact Book transaction identity.
        expected = getattr(sim, 'recovery_book_receipts', {}).get(operation)
        recorded = sim.book.operations.get(operation)
        # A funded Book debit without its exact sidecar receipt is an
        # incomplete checkpoint, not evidence that the rest was unfunded.
        # Unfunded rest has neither a Book operation nor a funded receipt.
        if (recorded is None) != (expected is None):
            raise ValueError('recovery receipt/Book checkpoint mismatch')
        if expected is not None and recorded[1] != expected:
            raise ValueError('recovery receipt/Book checkpoint mismatch')
        return sim.recovery_receipts[operation]
    # A funded sidecar without its event receipt is also an incomplete
    # checkpoint, even when the Book operation was lost during restore.
    # Never silently create another rest under that identity.
    if operation in getattr(sim, 'recovery_book_receipts', {}):
        raise ValueError('missing recovery replay receipt; restore checkpoint')
    # A Book debit without its corresponding rest receipt indicates an
    # incomplete checkpoint. Never repeat fatigue recovery on that identity.
    if operation in sim.book.operations:
        raise ValueError('missing recovery replay receipt; restore checkpoint')
    store = f'body_chemical:founder:{founder}'
    work = f'founder:{founder}'
    heat = f'body_heat:founder:{founder}'
    available = sim.book.energy.get(store, 0.)
    # All participants in a funded transfer must be valid before Book.move.
    # A corrupt destination balance must not create or destroy chemical fuel.
    for account in (work, heat):
        balance = sim.book.energy.get(account, 0.)
        if (isinstance(balance, bool) or not isinstance(balance, (int, float))
                or not isfinite(balance) or balance < 0):
            raise ValueError('invalid recovery destination fuel')
    # A damaged checkpoint must not allow free fatigue recovery while the
    # authoritative stored-fuel account contains an invalid quantity.
    if isinstance(available, bool) or not isinstance(available, (int, float)) or not isfinite(available) or available < 0:
        raise ValueError('invalid stored chemical fuel')
    mobilized = min(.012, available) if available >= .001 - 1e-9 else 0.
    txn = None
    if mobilized:
        # A conservative chemical-energy reallocation: 95% usable, 5% heat.
        # Energy transfers are balanced: body store -> existing Book accounts.
        txn = sim.book.move(energy=[(store, work, .95*mobilized),
                                    (store, heat, .05*mobilized)],
                            operation_id=operation)
    state.fatigue = max(0., state.fatigue - .20)
    state.rest_decisions += 1
    event = sim.log('founder_physiological_rest', founder, parent,
                    txn=txn, mobilized=mobilized, fatigue=state.fatigue,
                    recovery_decision_id=decision_id)
    sim.recovery_receipts[operation] = event
    if txn is not None:
        if not hasattr(sim, 'recovery_book_receipts'):
            sim.recovery_book_receipts = {}
        sim.recovery_book_receipts[operation] = txn
    return event
