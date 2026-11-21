"""Read-only normalization across independently developed Social/World branches.

No attempt to inject a later model into an older engine's internals.
State fields that do not exist are explicitly null, rather than invented.
"""
from __future__ import annotations

def describe_branch(sim):
    from founders_civ.experimental.social_agents import SocialSimulation
    from founders_civ.experimental.world_integration import IntegratedWorld
    from founders_civ.experimental.world024 import CommonsWorld
    if isinstance(sim,CommonsWorld): branch='WORLD-024'
    elif isinstance(sim,IntegratedWorld):branch='WORLD-022/023'
    elif isinstance(sim,SocialSimulation):branch='SOCIAL-021'
    else:raise TypeError(f'unsupported simulation class {type(sim).__name__}')
    book=sim.book
    trees=getattr(getattr(sim,'world_trees',None),'worlds',{})
    plants=getattr(getattr(sim,'seeds',None),'plants',{})
    return {
        'schema':'founders.integration.branch/1.0',
        'branch':branch,
        'cycle':sim.tick,
        'founders':len(sim.founders.people),
        'energy_accounts':len(book.energy),
        'material_accounts':len(book.mass),
        'tree_ids':sorted(trees),
        'plant_ids':sorted(plants),
        'factions':len(sim.factions),
        'cumulative_events':len(sim.events),
        'conservation':book.audit(),
        'not_supported':(['world_trees','seed_blueprints'] if branch=='SOCIAL-021' else []),
    }
