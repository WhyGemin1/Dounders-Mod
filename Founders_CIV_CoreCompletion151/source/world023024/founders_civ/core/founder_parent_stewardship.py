"""C018: voluntary, Book-funded care for the Realm supporting personal Trees.

The policy acts on *observed* parent reserve, not omniscient Book state.
Founders with living descendants have a reason to help maintain the parent
Realm; no owner, volunteer, or Tree receives free energy, biomass, or CE.
One Tree still cannot feed 100 Founders. Failure is possible and testable.
"""
from __future__ import annotations
import math

OBSERVATION_SITES = frozenset(('house', 'riverbank'))


def dependent_parent_ids(sim, founder):
    """Stable Realms owned by founder or hosting their active World Trees."""
    person = sim.founders.people.get(founder)
    if person is None or not person.alive:
        return ()
    parents = set()
    for cid, plant in sim.seeds.plants.items():
        if plant['status'] != 'stable':
            continue
        if plant['kind'] == 'realm' and plant['owner'] == founder:
            parents.add(cid)
        if plant['kind'] == 'world' and plant['owner'] == founder:
            parent_id = plant['parent']
            parent = sim.seeds.plants.get(parent_id)
            if parent and parent['status'] == 'stable' and parent['kind'] == 'realm':
                parents.add(parent_id)
    return tuple(sorted(parents))


def propose_parent_stewardship(sim, founder):
    if not getattr(sim, 'founder_parent_stewardship_enabled', False):
        return []
    person = sim.founders.people.get(founder)
    if person is None or not person.alive:
        return []
    proposals = []
    for rid in dependent_parent_ids(sim, founder):
        realm = sim.seeds.plants[rid]
        knowledge = sim.seeds.owner_reserve_knowledge.get(rid, {}).get(founder)
        # Founders must inspect locally before acting on changing reserves.
        if knowledge is None or sim.tick - knowledge['tick'] > 4:
            if person.location in OBSERVATION_SITES:
                proposals.append((5.40, 'parent_inspect', None, rid))
            elif sim.book.energy.get(f'founder:{founder}', 0.) >= .055 - 1e-8:
                # Offer the *existing physical movement action*, never a
                # teleport or a compelled maintenance transaction. The graph
                # permits ridge -> riverbank and fields -> house in one step.
                destination = ('riverbank' if person.location == 'ridge' else
                               'house' if person.location == 'fields' else None)
                if destination is not None:
                    proposals.append((2.75, 'move', None, destination))
            continue
        # A remembered reserve does not authorize remote physical work.
        # With an observed shortage, a dependent Founder may voluntarily
        # travel to inspect/tend; moving is Book-funded and does not maintain
        # the Realm. A distant owner can always choose another action.
        if person.location not in OBSERVATION_SITES:
            predicted = max(0., knowledge['reserve'] -
                            (sim.tick - knowledge['tick']) * realm['upkeep'])
            if (predicted < 7.0 * realm['upkeep'] and
                    sim.book.energy.get(f'founder:{founder}', 0.) >= .055 - 1e-8):
                destination = ('riverbank' if person.location == 'ridge' else
                               'house' if person.location == 'fields' else None)
                if destination is not None:
                    proposals.append((3.10, 'move', None, destination))
            continue
        predicted = max(0., knowledge['reserve'] -
                        (sim.tick - knowledge['tick']) * realm['upkeep'])
        if predicted >= 5.0 * realm['upkeep']:
            continue
        existing = sim.book.energy.get(f'founder:{founder}', 0.)
        # Preserve an embodied fuel reserve. Resource scarcity can prevent aid.
        available = max(0., existing - .12)
        # Fund only the observed five-day shortfall (minimum viable transfer),
        # rather than draining the Founder by the maximum on every visit.
        # This preserves chemical fuel for digestion, travel and later care.
        shortfall = max(0., 5.0 * realm['upkeep'] - predicted)
        amount = round(min(.60, available, max(.15, shortfall)), 8)
        if amount < .15:
            continue
        # A dependent Tree gives a concrete private incentive to maintain
        # the shared parent, above speculative new Tree research.
        urgency = min(1.5, (5 * realm['upkeep'] - predicted) / max(.01, realm['upkeep']))
        proposals.append((6.15 + urgency, 'parent_steward', None, (rid, amount)))
    return proposals


def inspect_parent(sim, founder, realm_id):
    if not getattr(sim, 'founder_parent_stewardship_enabled', False):
        raise ValueError('parent stewardship disabled')
    person = sim.founders.people.get(founder)
    if person is None or not person.alive or person.location not in OBSERVATION_SITES:
        raise ValueError('Realm inspection requires a living Founder at a site')
    if realm_id not in dependent_parent_ids(sim, founder):
        raise ValueError('Founder has no standing to inspect this parent Realm')
    reserve = sim.book.energy.get(f'reserve:{realm_id}', 0.)
    sim.seeds.owner_reserve_knowledge.setdefault(realm_id, {})[founder] = {
        'tick': sim.tick, 'reserve': reserve}
    return sim.log('founder_parent_realm_inspected', founder,
                   parent=getattr(sim, '_current_parent', None),
                   creation=realm_id, reserve=round(reserve, 8))


def tend_parent(sim, founder, target, decision_id):
    if not getattr(sim, 'founder_parent_stewardship_enabled', False):
        raise ValueError('parent stewardship disabled')
    person = sim.founders.people.get(founder)
    if person is None or not person.alive:
        raise ValueError('active Founder required')
    if not isinstance(target, (tuple, list)) or len(target) != 2:
        raise ValueError('invalid stewardship target')
    realm_id, amount = target
    if not isinstance(realm_id, str) or realm_id not in dependent_parent_ids(sim, founder):
        raise ValueError('not a dependent active parent Realm')
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount) or not .15 <= amount <= .60:
        raise ValueError('invalid stewardship amount')
    if not isinstance(decision_id, str) or not 1 <= len(decision_id) <= 56:
        raise ValueError('explicit valid decision identity required')
    receipt = f'parent:steward:{realm_id}:{founder}:{decision_id}'
    if receipt in sim.book.operations:
        # Replay must go through the same authoritative Book identity check.
        # Returning a cached receipt directly would accept a different amount
        # under the same decision ID without paying or flagging the conflict.
        return sim.book.move(energy=[(f'founder:{founder}', f'reserve:{realm_id}', amount)],
                             operation_id=receipt)
    # New physical transfers require local access; past Book receipts replay anywhere.
    if person.location not in OBSERVATION_SITES:
        raise ValueError('Realm stewardship requires local physical access')
    knowledge = sim.seeds.owner_reserve_knowledge.get(realm_id, {}).get(founder)
    if knowledge is None or sim.tick - knowledge['tick'] > 4:
        raise ValueError('fresh parent reserve observation required')
    current = sim.book.energy.get(f'founder:{founder}', 0.)
    if current + 1e-9 < amount + .12:
        raise ValueError('insufficient existing Founder chemical work reserve')
    txn = sim.book.move(energy=[(f'founder:{founder}', f'reserve:{realm_id}', amount)],
                        operation_id=receipt)
    sim.seeds.constructs.events.append({'event':'voluntary_parent_stewardship','id':realm_id,
                                        'actor':founder,'amount':amount})
    sim.seeds.owner_reserve_knowledge.setdefault(realm_id, {})[founder] = {
        'tick': sim.tick, 'reserve': sim.book.energy[f'reserve:{realm_id}']}
    sim.log('founder_parent_realm_tended', founder,
            parent=getattr(sim, '_current_parent', None), txn=txn,
            creation=realm_id, amount=amount)
    return txn
