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
    """Resolve physical food origin through the existing shared Book provenance.

    TreeResourceOps may create real food directly without C003 provisioning.
    Those lots are already recognized for harvesting and voluntary exchange;
    nutrition must not silently make the same owned food inedible.
    """
    from founders_civ.core.founder_exchange import _origin
    return _origin(sim, 'food', lot)


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
    from founders_civ.core.founder_exchange import owned_lots
    # A lot already ingested is no longer in portable holdings, but it remains
    # privately identifiable in this Founder's real Book ingestion receipt.
    ingested = {key[len('food:ingest:'):-len(':'+founder)]
                for key in book.operations
                if key.startswith('food:ingest:') and key.endswith(':'+founder)}
    for lot in sorted(set(owned_lots(sim, founder, 'food')) | ingested):
        tree_id, tree = _tree_for_lot(sim, lot)
        if tree is None or getattr(tree, 'book', None) is not book:
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
    # Validate the explicitly targeted Tree before resolving lot provenance.
    # The origin resolver deliberately ignores detached Books; report that
    # integrity violation directly rather than misclassifying a known lot.
    targeted_tree = sim.world_trees.worlds.get(tree_id)
    if targeted_tree is not None and getattr(targeted_tree, 'book', None) is not sim.book:
        raise ValueError('Tree does not share the authoritative Book')
    actual_id, tree = _tree_for_lot(sim, lot)
    if actual_id != tree_id or tree is None:
        raise ValueError('unknown identified food lot')
    if getattr(tree, 'book', None) is not sim.book:
        raise ValueError('Tree does not share the authoritative Book')
    from founders_civ.core.founder_exchange import owns_lot
    # A completed ingestion consumed the portable holding; a retry must be
    # resolved by this Founder's exact Book receipt, not rejected as theft.
    # New ingestion still requires real current ownership.
    ingested_id = f'food:ingest:{lot}:{founder}'
    if (action == 'food_ingest' and ingested_id not in sim.book.operations
            and not owns_lot(sim, founder, 'food', lot)):
        raise ValueError('Founder never harvested or received this food lot')
    if action == 'food_digest' and f'food:ingest:{lot}:{founder}' not in sim.book.operations:
        raise ValueError('Founder has not ingested identified food lot')
    # The Book commits both physical transfers and their permanent operation IDs.
    # A retried call may return the original transaction, but it must not
    # manufacture a second social event or second learning experience.
    receipt = (f'food:ingest:{lot}:{founder}' if action == 'food_ingest'
               else f'food:digest:{lot}:{founder}')
    was_committed = receipt in sim.book.operations
    if action == 'food_ingest':
        txn = tree.resources.eat_food(lot, founder)
        event_name = 'founder_food_ingested'
    else:
        txn = tree.resources.digest_food(lot, founder)
        event_name = 'founder_food_digested'
    if not was_committed:
        sim.log(event_name, founder, parent=getattr(sim, '_current_parent', None),
                txn=txn, creation=tree_id, lot=lot)
    return txn
