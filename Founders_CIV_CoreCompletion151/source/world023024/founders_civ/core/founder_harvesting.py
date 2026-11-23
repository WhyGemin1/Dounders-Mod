"""U026-C004: Founder-informed access to real Tree-owned food and fruit lots.

The observation is an information snapshot, not omniscience or a reservation.
Only a Founder physically at the riverbank can take a known lot; the Book
provides the authoritative atomic transfer, identity, and replay safeguards.
No energy points are charged for proposing or transferring ownership. This is
an optional capability for Trees with C003 provisioning, not WorldBox gameplay.
"""
from __future__ import annotations

MAX_STALENESS=6

def _recent_observation(sim, evidence):
    """Reject malformed/future perception timestamps before any proposal or transfer."""
    if not isinstance(evidence, dict):
        return False
    seen = evidence.get('seen_tick')
    tick = getattr(sim, 'tick', None)
    return (type(seen) is int and type(tick) is int and
            0 <= tick - seen <= MAX_STALENESS)



def _known_entries(evidence):
    """Treat corrupted checkpoint perceptions as unavailable, never as actions."""
    if not isinstance(evidence, dict):
        return ()
    entries = evidence.get('known_lots', ())
    if not isinstance(entries, (list, tuple)):
        return ()
    return tuple(entry for entry in entries
                 if isinstance(entry, dict)
                 and isinstance(entry.get('lot'), str)
                 and entry.get('kind') in ('food', 'fruit'))


def observed_lots(tree):
    """Take a bounded, current snapshot when a Founder actually observes a Tree."""
    policy=tree.provisioning
    if policy is None:return []
    lots=getattr(policy, 'lots', None)
    if not isinstance(lots, dict):return []
    available=[]
    for lot,record in sorted(lots.items(), key=lambda pair: str(pair[0])):
        if not isinstance(lot, str) or not lot:continue
        if not all(hasattr(record, field) for field in ('kind', 'created', 'state')):continue
        # Observation must not advertise checkpoint-corrupt food or fruit.
        # This is perception filtering only; perform_harvest remains the
        # authoritative, independently checked Book transfer boundary.
        if record.kind not in ('food', 'fruit'):continue
        if type(record.created) is not int or record.created < 0:continue
        if type(tree.age) is not int or tree.age < record.created:continue
        if record.kind == 'food' and record.state != 'stored':continue
        if record.kind == 'fruit' and (
            record.state != 'mature' or
            type(getattr(policy, 'maturity_days', None)) is not int or
            policy.maturity_days < 0 or
            tree.age - record.created < policy.maturity_days):continue
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
    # C026: prioritize known edible food over propagation fruit when depleted.
    # This is a decision preference, never a fuel toll or inventory scan.
    usable=sim.book.energy[f'founder:{founder}']
    proposals=[]
    for tid,tree in sorted(sim.world_trees.worlds.items()):
        evidence=tree.observations.get(founder)
        if not _recent_observation(sim, evidence):continue
        for entry in _known_entries(evidence)[:10]:
            if entry.get('kind') not in ('fruit','food'):continue
            lot=entry.get('lot')
            if not isinstance(lot,str):continue
            # Deliberately do not consult the current lot balance or state here.
            # A stale observation can cause a rejected attempt, as in a real world.
            if entry['kind']=='food':
                score=2.35+.6*(goal in ('security','solidarity'))
                if usable < .19:score += 1.0
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
    # Every Tree must debit the one authoritative simulation Book. A detached
    # Tree Book would create untracked physical food or CE even when its local
    # balances appear valid; fail before touching either ledger.
    if tree.book is not sim.book:
        raise ValueError('Tree does not share the authoritative Book')
    evidence=tree.observations.get(founder)
    if (not _recent_observation(sim, evidence) or
        not any(x.get('lot')==lot and x.get('kind')==kind for x in _known_entries(evidence))):
        raise ValueError('resource not known through a recent observation')
    # A portable holding and its Book harvest receipt currently use the lot
    # name without the World ID. Fail closed before any transfer when another
    # World has the same local lot name; otherwise two physical origins could
    # be conflated by nutrition or voluntary exchange.
    from founders_civ.core.founder_exchange import _origin
    resolved_tree, _ = _origin(sim, kind, lot)
    if resolved_tree != tid:
        raise ValueError('ambiguous or unauthenticated cross-World resource lot')
    record=tree.provisioning.lots.get(lot)
    if record is None or record.kind!=kind:raise ValueError('unavailable identified resource lot')
    source=f'{"portable_food" if kind=="food" else "fruit"}:lot:{lot}:tree:{tid}'
    if (record.state not in ('stored','mature') or
        (kind=='food' and record.state!='stored') or
        (type(record.created) is not int or record.created < 0 or
         type(tree.age) is not int or tree.age < 0 or
         record.created > tree.age) or
        (kind=='fruit' and (record.state!='mature' or
          type(record.created) is not int or record.created < 0 or
          type(tree.age) is not int or tree.age - record.created < tree.provisioning.maturity_days)) or
        tree.book.mass[source]<=1e-9):
        # The Founder learns the specific lot is unavailable only by reaching
        # the claimed resource or personally attempting the transfer.
        if tree.book.mass[source]<=1e-9:record.state='transferred'
        evidence['known_lots']=[x for x in _known_entries(evidence) if x.get('lot')!=lot]
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
