"""U026-C015: opt-in autonomous consumption of Book-owned identified food.

This is the missing join between C004 Founder harvesting and C014 ingestion /
digestion. The policy reads the authoritative Book's *own-owner history*
rather than scanning unobserved Tree supplies. No independent inventory,
extra decision cost, time currency, or energy-from-rest is introduced.
The physical metabolism is intentionally synthetic; not native WorldBox.
"""
from __future__ import annotations


def _owned_harvests(book, founder):
    """Past successful harvest IDs, filtered to the requesting Founder."""
    suffix = ':' + founder
    prefix = 'food:harvest:'
    return sorted({key[len(prefix):-len(suffix)] for key in book.operations
                   if key.startswith(prefix) and key.endswith(suffix)})


def _tree_for_lot(sim, lot):
    # Resolve the lot's immutable producing Tree. Even a collapsed Tree may
    # retain food previously harvested by a Founder.
    for tree_id, tree in sorted(sim.world_trees.worlds.items()):
        if tree.provisioning is not None and lot in tree.provisioning.lots:
            if tree.provisioning.lots[lot].kind == 'food':
                return tree_id, tree
    return None, None


def propose_nutrition(sim, founder):
    if not getattr(sim, 'founder_nutrition_enabled', False):
        return []
    person = sim.founders.people.get(founder)
    if person is None or not person.alive:
        return []
    book = sim.book
    proposals = []
    # Each Founder can identify food they actually harvested; this is not
    # omniscient visibility into another actor's holdings or Tree inventory.
    for lot in _owned_harvests(book, founder):
        tree_id, tree = _tree_for_lot(sim, lot)
        if tree is None:
            continue
        holding = f'portable_food:lot:{lot}:founder:{founder}'
        gut = f'gut:founder:{founder}:lot:{lot}'
        ingest_id = f'food:ingest:{lot}:{founder}'
        digest_id = f'food:digest:{lot}:{founder}'
        if ingest_id not in book.operations and book.mass[holding] >= .08-1e-8:
            proposals.append((4.50, 'food_ingest', None, (tree_id, lot)))
        elif (ingest_id in book.operations and digest_id not in book.operations
              and book.mass[gut] >= .08-1e-8
              and (book.energy[f'founder:{founder}'] >= .001-1e-8
                   or book.energy[f'body_chemical:founder:{founder}'] >= .001-1e-8)):
            proposals.append((4.70, 'food_digest', None, (tree_id, lot)))
    return proposals


def perform_nutrition(sim, founder, action, target):
    if not getattr(sim, 'founder_nutrition_enabled', False):
        raise ValueError('Founder nutrition policy disabled')
    if action not in ('food_ingest', 'food_digest'):
        raise ValueError('invalid nutrition action')
    if not (isinstance(target, (tuple, list)) and len(target) == 2
            and all(isinstance(x, str) for x in target)):
        raise ValueError('invalid nutrition target')
    person = sim.founders.people.get(founder)
    if person is None or not person.alive:
        raise ValueError('active Founder required')
    tree_id, lot = target
    actual_id, tree = _tree_for_lot(sim, lot)
    if actual_id != tree_id or tree is None:
        raise ValueError('unknown identified food lot')
    if f'food:harvest:{lot}:{founder}' not in sim.book.operations:
        raise ValueError('Founder never harvested this food lot')
    if action == 'food_ingest':
        txn = tree.resources.eat_food(lot, founder)
        event_name = 'founder_food_ingested'
    else:
        txn = tree.resources.digest_food(lot, founder)
        event_name = 'founder_food_digested'
    sim.log(event_name, founder, parent=getattr(sim, '_current_parent', None),
            txn=txn, creation=tree_id, lot=lot)
    return txn
