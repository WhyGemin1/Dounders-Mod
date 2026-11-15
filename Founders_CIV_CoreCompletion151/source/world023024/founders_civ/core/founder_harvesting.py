"""U026-C004: Founder-informed access to real Tree-owned food and fruit lots.

The observation is an information snapshot, not omniscience or a reservation.
Only a Founder physically at the riverbank can take a known lot; the Book
provides the authoritative atomic transfer, identity, and replay safeguards.
No energy points are charged for proposing or transferring ownership. This is
an optional capability for Trees with C003 provisioning, not WorldBox gameplay.
"""
from __future__ import annotations

MAX_STALENESS=6


def observed_lots(tree):
    """Take a bounded, current snapshot when a Founder actually observes a Tree."""
    policy=tree.provisioning
    if policy is None:return []
    available=[]
    for lot,record in sorted(policy.lots.items()):
        if record.state not in ('stored','mature'):continue
        if record.kind=='fruit' and record.state!='mature':continue
        kind=record.kind
        source=f'{"portable_food" if kind=="food" else "fruit"}:lot:{lot}:tree:{tree.id}'
        if tree.book.mass[source]<=1e-9:continue
        available.append({'lot':lot,'kind':kind,'observed_tree_age':tree.age})
    return available


def propose_harvest(sim, founder):
    """Use ONLY previously perceived lots; do not inspect current Book for choice."""
    if not getattr(sim,'founder_harvest_enabled',False):return []
    f=sim.founders.people[founder]
    if not f.alive or f.location!='riverbank':return []
    goal=sim.states[founder].main_goal
    proposals=[]
    for tid,tree in sorted(sim.world_trees.worlds.items()):
        evidence=tree.observations.get(founder)
        if evidence is None or not 0<=sim.tick-evidence.get('seen_tick',-10000)<=MAX_STALENESS:continue
        for entry in evidence.get('known_lots',())[:10]:
            if entry.get('kind') not in ('fruit','food'):continue
            lot=entry.get('lot')
            if not isinstance(lot,str):continue
            # Deliberately do not consult the current lot balance or state here.
            # A stale observation can cause a rejected attempt, as in a real world.
            if entry['kind']=='food':
                score=2.35+.6*(goal in ('security','solidarity'))
            else:
                score=2.45+.75*(goal in ('research','exploration','leadership'))
            proposals.append((score,'tree_harvest',None,(tid,lot,entry['kind'])))
    return proposals


def perform_harvest(sim,founder,target):
    """Check physical access and last perception; then move exactly one lot."""
    if not getattr(sim,'founder_harvest_enabled',False):
        raise ValueError('Founder harvest policy disabled')
    if not (isinstance(target,(tuple,list)) and len(target)==3):
        raise ValueError('malformed resource target')
    tid,lot,kind=target
    if kind not in ('fruit','food'):raise ValueError('unknown resource kind')
    f=sim.founders.people.get(founder)
    if f is None or not f.alive or f.location!='riverbank':
        raise ValueError('Founder is not physically at the riverbank')
    tree=sim.world_trees.worlds.get(tid)
    if tree is None or tree.provisioning is None:raise ValueError('unknown resource Tree')
    evidence=tree.observations.get(founder)
    if (evidence is None or not 0<=sim.tick-evidence.get('seen_tick',-10000)<=MAX_STALENESS or
        not any(x.get('lot')==lot and x.get('kind')==kind for x in evidence.get('known_lots',()))):
        raise ValueError('resource not known through a recent observation')
    record=tree.provisioning.lots.get(lot)
    if record is None or record.kind!=kind:raise ValueError('unavailable identified resource lot')
    source=f'{"portable_food" if kind=="food" else "fruit"}:lot:{lot}:tree:{tid}'
    if (record.state not in ('stored','mature') or (kind=='fruit' and record.state!='mature') or
        tree.book.mass[source]<=1e-9):
        # The Founder learns the specific lot is unavailable only by reaching
        # the claimed resource or personally attempting the transfer.
        if tree.book.mass[source]<=1e-9:record.state='transferred'
        evidence['known_lots']=[x for x in evidence['known_lots'] if x.get('lot')!=lot]
        raise ValueError('resource no longer available')
    # No arbitrary decision/transfer cost; real labor physiology is separate.
    if kind=='fruit':txn=tree.resources.harvest_fruit(lot,founder)
    else:txn=tree.resources.harvest_food(lot,founder)
    record.state='transferred'
    evidence['known_lots']=[x for x in evidence['known_lots'] if x.get('lot')!=lot]
    sim.log('tree_founder_harvest',founder,parent=getattr(sim,'_current_parent',None),
            txn=txn,creation=tid,lot=lot,resource_kind=kind,
            observed_at_tick=evidence['seen_tick'])
    return txn
