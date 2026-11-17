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


def paid_work(sim, founder, action, base_cost):
    """Pay only for actual work; fatigue degrades fuel efficiency.

    This opt-in policy does not alter the legacy SOCIAL-021 control arm.
    Failed work payments do not change fatigue or Book accounts.
    """
    if not isfinite(base_cost) or base_cost < 0:
        raise ValueError('invalid work cost')
    state = state_for(sim, founder)
    cost = base_cost * (1.0 + 0.6 * state.fatigue)
    account = f'founder:{founder}'
    if sim.book.energy[account] + 1e-10 < cost:
        return False
    if cost <= 0:
        return None
    txn = sim.book.move(energy=[(account, 'environment:heat', cost)])
    state.fatigue = min(1., state.fatigue + 0.03 + 0.16 * cost)
    return txn


def propose_rest(sim, founder):
    person = sim.founders.people.get(founder)
    if person is None or not person.alive:
        return []
    state = state_for(sim, founder)
    usable = sim.book.energy[f'founder:{founder}']
    stored = sim.book.energy.get(f'body_chemical:founder:{founder}', 0.)
    # Even with no work fuel, rest remains an available *choice*.
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
    # Rest is a chosen physical action, not a purchase of elapsed time.
    # Replay identity comes from the exact decision, NOT the simulation tick.
    if decision_id is None:
        decision_id = parent if parent is not None else f'manual:{sim.next_event + 1}'
    if not isinstance(decision_id, str) or not 1 <= len(decision_id) <= 72:
        raise ValueError('invalid recovery decision ID')
    operation = f'founder:rest:{founder}:{decision_id}'
    if operation in sim.recovery_receipts:
        return sim.recovery_receipts[operation]
    store = f'body_chemical:founder:{founder}'
    work = f'founder:{founder}'
    heat = f'body_heat:founder:{founder}'
    available = sim.book.energy.get(store, 0.)
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
    return event
