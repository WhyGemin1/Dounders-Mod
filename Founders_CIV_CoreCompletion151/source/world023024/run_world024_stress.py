"""Run a preregistered WORLD-024 scenario; 100 Founders share one rooted tree.
Scenarios are synthetic, repeatable and label their stress settings explicitly.
"""
import argparse, json, time
from pathlib import Path
from run_world_tree_pilot import bootstrap
from founders_civ.experimental.world024 import CommonsWorld

PROFILES={
 'commons': dict(governance='collective',extraction='careful',allow_private=False),
 'owner_only': dict(governance='owner',extraction='careful',allow_private=False),
 'fragmented': dict(governance='fragmented',extraction='careful',allow_private=False),
 'unmaintained': dict(governance='none',extraction='careful',allow_private=False),
 'extractive': dict(governance='collective',extraction='intensive',allow_private=False),
 'dry_season': dict(governance='collective',extraction='careful',allow_private=False),
 'disease': dict(governance='collective',extraction='careful',allow_private=False),
 'upkeep_spike': dict(governance='collective',extraction='careful',allow_private=False),
 'labor_shock': dict(governance='collective',extraction='careful',allow_private=False),
 'private_option': dict(governance='collective',extraction='careful',allow_private=True),
}
STRESSES={
 'dry_season': dict(rainfall=.16,start=20,end=120),
 'disease': dict(disease=.025,start=30,end=150),
 'upkeep_spike': dict(upkeeps=2.1,start=18,end=125),
 'labor_shock': dict(founder_drain=.035,start=22,end=115),
}

def run(seed, cycles, profile, captures=False):
    t=time.perf_counter()
    opts=PROFILES[profile]
    def factory(**kw):return CommonsWorld(**kw,**opts)
    sim,realm,tree=bootstrap(seed=seed,simulator_class=factory)
    sim.mark_shared(tree)
    if profile in STRESSES:sim.set_stress(**STRESSES[profile])
    history=[]
    for i in range(cycles):
        sim.step()
        if i%20==19 or i==cycles-1:
            world=sim.world_trees.worlds[tree]
            history.append({'cycle':i+1,'population':world.population,'state':world.state,
                  'plant_biomass':world.timeline[-1]['plants'],'stewards':len(sim.stewards),
                  'energy_from_tree':round(sim.food_energy,4),
                  'harvest':round(sim.harvest_mass,4)})
    results=sim.summary_024();results['duration']=cycles;results['profile']=profile
    results['elapsed_s']=round(time.perf_counter()-t,2)
    results['history']=history if captures else None
    results['tree_collapse_cycle']=next((e['tick']-3 for e in sim.events if e['action']=='creation_collapsed' and e.get('creation')==tree),None)
    results['realm_collapse_cycle']=next((e['tick']-3 for e in sim.events if e['action']=='creation_collapsed' and e.get('creation')==realm),None)
    results['world_decisions']=dict((k,v) for k,v in sim.counter.items() if k in ('tree_food_harvested','tree_food_consumed','commons_enlisted','commons_maintained','commons_observed','private_blueprint_drafted','seed_planted','creation_collapsed','tree_disease'))
    if captures:
        results['decision_examples']=[e for e in sim.events if e['action'] in ('commons_enlisted','commons_maintained','tree_food_harvested','tree_food_consumed','private_blueprint_drafted','creation_collapsed')][:25]
    return results

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--seed',type=int,default=400)
    p.add_argument('--cycles',type=int,default=120)
    p.add_argument('--profile',choices=PROFILES,default='commons')
    p.add_argument('--out',type=Path)
    p.add_argument('--history',action='store_true')
    a=p.parse_args()
    ans=run(a.seed,a.cycles,a.profile,a.history)
    if a.out:
        a.out.parent.mkdir(exist_ok=True,parents=True)
        a.out.write_text(json.dumps(ans,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in ans.items() if k not in ('history','conservation','decision_examples')},indent=2))
