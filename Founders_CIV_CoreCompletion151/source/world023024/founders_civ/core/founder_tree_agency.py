"""U026-C017: encourage Founders to create *their own* food-producing World Trees.

This policy neither shares one Tree's food among all 100 Founders nor creates
any biomass, chemical fuel, or fictional Creation Energy. Plans are voluntary;
fruit, peer review, existing parent realms, material, and work must be funded
through the single Book. A Founder can fail to establish their Tree.
"""
from __future__ import annotations


def _stable_worlds(sim, founder):
    return [c for c in sim.seeds.plants.values()
            if c['kind'] == 'world' and c['owner'] == founder and c['status'] == 'stable']


def _own_blueprint(sim, founder):
    return next((b for b in sim.seeds.blueprints.values()
                 if b.author == founder and b.kind == 'world'
                 and b.stage != 'planted'), None)


def _realm_to_develop(sim):
    """Pick a preexisting parent with the fewest active World Trees.

    The number of Worlds is *not* a food source; this only spreads physical
    Tree creations across viable parents rather than packing one parent.
    """
    realms = [c for c in sim.seeds.plants.values()
              if c['kind'] == 'realm' and c['status'] == 'stable']
    if not realms:
        return None
    def load(realm):
        return sum(p['kind'] == 'world' and p['status'] == 'stable'
                   and p['parent'] == realm['id'] for p in sim.seeds.plants.values())
    return min(realms, key=lambda r: (load(r), r['id']))['id']


def _own_fruit(sim, founder):
    """Fruit personally harvested OR accepted through a real Book agreement."""
    from founders_civ.core.founder_exchange import owned_lots, _origin
    for lot in owned_lots(sim, founder, 'fruit'):
        tid, tree = _origin(sim, 'fruit', lot)
        if tree is not None:
            yield tid, lot


def propose_self_trees(sim, founder, contacts):
    if not getattr(sim, 'founder_tree_independence_enabled', False):
        return []
    person = sim.founders.people.get(founder)
    if person is None or not person.alive:
        return []
    # Existing Tree ownership is NOT an arbitrary prohibition on founding
    # another Tree. A new proposal still needs the Founder to possess a
    # different physical, CE-backed fruit and must pass the ordinary
    # research, consent, Book-funding and habitat resource preflights.
    b = _own_blueprint(sim, founder)
    energy = sim.book.energy.get(f'founder:{founder}', 0.)
    # Proposal affordability must not overdraw physical fuel even by an epsilon.
    # No work spent merely on deciding whether to design a Tree.
    if b is None:
        # React to self-acquired propagation material, NOT a centralized
        # "100 Founders must plant 100 Trees" goal. Competing over one
        # Tree's few fruits does not justify hundreds of research projects.
        if not any(_own_fruit(sim, founder)):
            return []
        parent = _realm_to_develop(sim)
        if parent is None or energy < .08:
            return []
        if len(sim.seeds.plants) + len(sim.seeds.blueprints) >= 106:
            return []  # bounded research proposals; physical funding still decides
        return [(4.35, 'seed_design', None, ('world', parent))]
    if b.parent_id not in sim.seeds.plants or sim.seeds.plants[b.parent_id]['status'] != 'stable':
        return []
    if b.stage in ('draft','researching'):
        # Two independent research observations suffice for this synthetic
        # blueprint. Further identical research would only waste finite fuel.
        if b.stage == 'researching' and len(b.research_ticks) >= 2:
            # A poor first contact must not hide another willing, funded peer.
            # Stable ID ordering makes proposals independent of contact iteration order.
            peers = sorted({p for p in contacts if p != founder and p in sim.founders.people
                            and sim.founders.people[p].alive
                            and sim.founders.people[p].location == person.location
                            and sim.book.energy.get(f'founder:{p}', 0.) >= .11})
            if peers:
                return [(5.1, 'seed_request_review', peers[0], b.id)]
            return []
        if sim.tick not in b.research_ticks and energy >= .18:
            return [(4.6, 'seed_research', None, b.id)]
        return []
    if b.stage != 'validated':
        return []
    # A real collected fruit lot containing finite CE is a prerequisite to
    # constructing a new food Tree; proposal priority cannot bypass funding.
    if f'seed:fund:{b.id}' not in sim.book.operations:
        if energy < .01:
            return []
        fruits = list(_own_fruit(sim, founder))
        return [(5.3, 'seed_fund', None, (b.id, tid, lot)) for tid, lot in fruits[:1]]
    if (energy >= 1.0
            and sim.book.mass.get('soil:Solara:grassland',0.) >= 1.1
            and sim.book.energy.get('house',0.) >= 2.25):
        return [(5.6, 'seed_plant', None, b.id)]
    return []


def fund_own_tree(sim, founder, target):
    if not getattr(sim, 'founder_tree_independence_enabled', False):
        raise ValueError('own-Tree Creation policy disabled')
    if not (isinstance(target,(tuple,list)) and len(target)==3):
        raise ValueError('invalid fruit-funded Tree target')
    blueprint_id, tree_id, lot = target
    b = sim.seeds.blueprints.get(blueprint_id)
    if b is None or b.kind != 'world' or b.author != founder or b.stage != 'validated':
        raise ValueError('only an author can fund their validated World blueprint')
    tree = sim.world_trees.worlds.get(tree_id)
    if tree is None or tree.provisioning is None or lot not in tree.provisioning.lots:
        raise ValueError('unknown real fruit lot')
    if tree.provisioning.lots[lot].kind != 'fruit':
        raise ValueError('only Creation fruit funds the World seed')
    from founders_civ.core.founder_exchange import owns_lot
    # Identical retry of a successfully funded seed is Book-idempotent even
    # after the fruit was consumed. Check the original physical source so an
    # unrelated fruit cannot reuse the same blueprint identity.
    funded = sim.book.operations.get(f'seed:fund:{blueprint_id}')
    previous_source = f'fruit:lot:{lot}:founder:{founder}'
    previous_ce = f'ce:fruit:lot:{lot}:founder:{founder}'
    replay_owned = bool(funded and any(leg[0] == previous_source for leg in funded[1].material)
                        and any(leg[0] == previous_ce for leg in funded[1].energy))
    if not owns_lot(sim, founder, 'fruit', lot) and not replay_owned:
        raise ValueError('Founder does not own identified fruit')
    # Calls the existing transactional Book path, keeping fruit and CE distinct.
    already = f'seed:fund:{blueprint_id}' in sim.book.operations
    result = tree.resources.fund_world_seed(lot, founder, blueprint_id)
    if not already:
        sim.log('founder_own_tree_seed_funded', founder,
            parent=getattr(sim,'_current_parent',None), txn=result,
            blueprint=blueprint_id, source_tree=tree_id, fruit_lot=lot)
    return result


def prioritize_propagation(sim, founder, proposals):
    """Prefer harvesting *locally observed* seed fruit over hoarding plans.

    Does not grant observation, transfer a lot, or inspect any other Founder's
    inventory. Only C004's normal physical harvest authorization can succeed.
    """
    if not getattr(sim, 'founder_tree_independence_enabled', False):
        return proposals
    if any(_own_fruit(sim, founder)):
        return proposals
    out=[]
    for score,action,target,meta in proposals:
        if (action=='tree_harvest' and isinstance(meta,(list,tuple))
                and len(meta)==3 and meta[2]=='fruit'):
            score += 2.75
        out.append((score,action,target,meta))
    return out
