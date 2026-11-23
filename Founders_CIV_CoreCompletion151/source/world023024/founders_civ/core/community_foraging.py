"""U026-C017: autonomous, situated food discovery and fuel-aware decisions.

A Founder can see portable Tree goods at a connected riverbank without paying
an arbitrary work tariff simply to perceive them. This is *not* remote access to
Book holdings or shared omniscient knowledge: the observation is founder-owned,
site-limited, short-lived, and harvest authorization remains in C004.

No new matter or energy is generated, and no time units are bought or spent.
"""
from __future__ import annotations

from founders_civ.core.founder_harvesting import MAX_STALENESS, observed_lots


def _accessible(sim, founder, tid):
    person = sim.founders.people.get(founder)
    tree = sim.world_trees.worlds.get(tid)
    return bool(person is not None and person.alive
                and person.location == 'riverbank'
                and tree is not None and tree.state == 'active'
                and getattr(tree, 'book', None) is sim.book
                and isinstance(getattr(sim.seeds, 'plants', None), dict)
                and isinstance(sim.seeds.plants.get(tid), dict)
                and sim.seeds.plants[tid].get('status') == 'stable'
                and tree.provisioning is not None)


def propose_community_scan(sim, founder):
    """Low-work Founders may inspect *visible* food on their actual riverbank.

    The proposal never exposes lot IDs or balances. Those are perceived only
    when `perform_community_scan` executes at the physical location.
    """
    if not getattr(sim, 'founder_community_foraging_enabled', False):
        return []
    candidates = []
    for tid, tree in sorted(sim.world_trees.worlds.items()):
        if not _accessible(sim, founder, tid):
            continue
        seen = tree.observations.get(founder)
        if seen is not None and 0 <= sim.tick - seen['seen_tick'] <= MAX_STALENESS:
            continue
        # A visible Tree is sensed locally; its inventories are not consulted.
        # No role/owner restriction: this is passive inspection, not stewardship.
        candidates.append((3.85, 'food_scan', None, tid))
    return candidates[:1]  # bounded decisions: no infinite sensing agenda


def perform_community_scan(sim, founder, tid):
    if not getattr(sim, 'founder_community_foraging_enabled', False):
        raise ValueError('community foraging disabled')
    if not isinstance(tid, str) or not _accessible(sim, founder, tid):
        raise ValueError('Tree not physically observable from riverbank')
    tree = sim.world_trees.worlds[tid]
    # The actual resource sensor is shared with the C004 observation contract.
    # It includes only physically present, Tree-owned, mature goods.
    lots = observed_lots(tree)
    prior = tree.observations.get(founder) or {}
    snapshot = dict(prior, seen_tick=sim.tick, known_lots=lots)
    # A passive inventory glimpse does not fabricate measurements of wildlife.
    tree.observations[founder] = snapshot
    return sim.log('founder_food_scan', founder,
                   parent=getattr(sim, '_current_parent', None),
                   creation=tid, visible_lots=len(lots))


def prioritize_food(sim, founder, proposals):
    """Prioritize physically observed food when usable fuel is low.

    This changes choice *ranking* only. It does not grant permission to harvest,
    mutate matter/energy, or bypass the Book's ownership/replay checks.
    """
    if not getattr(sim, 'founder_community_foraging_enabled', False):
        return proposals
    work = sim.book.energy.get(f'founder:{founder}', 0.)
    body = sim.book.energy.get(f'body_chemical:founder:{founder}', 0.)
    if work >= .24 and body >= .02:
        return proposals
    out = []
    for score, action, target, meta in proposals:
        if action == 'tree_harvest' and isinstance(meta, (tuple, list)) and len(meta) == 3:
            if meta[2] == 'food':
                score += 2.35
        elif action in ('food_ingest', 'food_digest'):
            score += 1.15
        out.append((score, action, target, meta))
    return out
