"""WORLD-023 vertical-slice reproducible showcase.

Research/plant setup uses the real seed API with a nominated Founder and
independent reviewer. Thereafter the simulation runs autonomously: no scripted
world repair or population replacement. Use --stress to compare multiple seeds.
"""
import argparse, json
from pathlib import Path
from founders_civ.experimental.world_integration import IntegratedWorld


def bootstrap(seed=400, simulator_class=IntegratedWorld):
    sim=simulator_class(seed=seed,days=20000)
    founder='F001'
    sim.creation_limit=3
    rs=sim.seeds
    realm_bp=rs.draft(founder,'realm','First Living Realm',x=64,y=42)
    rs.research(founder,realm_bp.id)
    sim.step()
    if sim.tick not in realm_bp.research_ticks:rs.research(founder,realm_bp.id)
    reviewer=next(a for a,f in sim.founders.people.items()
                  if a!=founder and f.location==sim.founders.people[founder].location)
    rs.validate(reviewer,realm_bp.id)
    realm=rs.plant(founder,realm_bp.id)
    founder=max(sim.founders.people, key=lambda a: (sim.book.energy[f'founder:{a}'],a))
    tree_bp=rs.draft(founder,'world','First Living World Tree',realm['id'],x=66,y=43)
    rs.research(founder,tree_bp.id)
    sim.step()
    if sim.tick not in tree_bp.research_ticks:rs.research(founder,tree_bp.id)
    reviewer=next(a for a,f in sim.founders.people.items()
                  if a!=founder and f.location==sim.founders.people[founder].location)
    rs.validate(reviewer,tree_bp.id)
    tree=rs.plant(founder,tree_bp.id)
    assert sim.world_trees.worlds[tree['id']].population==0, 'World Tree spawned life without Species Seed'
    # Species need their *own* researched and peer-reviewed creation blueprint.
    founder=max(sim.founders.people, key=lambda a: (sim.book.energy[f'founder:{a}'],a))
    sp=rs.draft(founder,'species','Founding Grazers',tree['id'],x=66.8,y=43.2)
    rs.research(founder,sp.id)
    sim.step()
    if sim.tick not in sp.research_ticks:rs.research(founder,sp.id)
    reviewer=next(a for a,f in sim.founders.people.items()
                  if a!=founder and f.location==sim.founders.people[founder].location)
    rs.validate(reviewer,sp.id)
    rs.plant(founder,sp.id)
    assert sim.world_trees.worlds[tree['id']].population==16
    return sim,realm['id'],tree['id']


def run(seed=400,days=120,log_events=False):
    sim,realm_id,tree_id=bootstrap(seed)
    for _ in range(days):sim.step()
    world=sim.world_trees.worlds[tree_id]
    events=[x for x in sim.events if x['action'].startswith('tree_') or x['action'] in ('creation_tended','creation_collapsed')]
    chosen=[x for x in sim.events if x['action']=='decision' and x['chosen'].startswith('tree_')]
    out={'seed':seed,'cycles':days,'tree_id':tree_id,'realm_id':realm_id,
         'tree_status':sim.seeds.plants[tree_id]['status'],
         'realm_status':sim.seeds.plants[realm_id]['status'],
         'world_age':world.age,'population':world.population,
         'births':world.counters['tree_birth'],'deaths':world.counters['tree_death'],
         'generations':sorted({r.generation for r in world.residents.values()}),
         'tree_observations':world.counters['tree_observed'],
         'tree_research':world.counters['tree_researched'],
         'tree_maintenance':sim.counter['tree_autonomous_maintenance'],
         'world_final':world.timeline[-1],
         'conservation':sim.book.audit(),
         'decisions':len(chosen),
         'trajectory':world.timeline}
    if log_events:out['events']=events
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--seed',type=int,default=400)
    p.add_argument('--days',type=int,default=120)
    p.add_argument('--out',type=Path)
    p.add_argument('--events',action='store_true')
    a=p.parse_args()
    x=run(a.seed,a.days,a.events)
    if a.out:
        a.out.parent.mkdir(exist_ok=True,parents=True)
        a.out.write_text(json.dumps(x,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in x.items() if k not in ('trajectory','events','conservation','world_final')},indent=2))
    print('conservation:',x['conservation'])
    print('final world:',x['world_final'])
