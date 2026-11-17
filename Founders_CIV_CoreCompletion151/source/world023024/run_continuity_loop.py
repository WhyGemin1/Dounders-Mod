"""v0.20 experimental four-system loop. Run from package root.
Uses v0.19 modules unchanged; shared Book unifies energy/material accounts.
All scheduling thresholds and interventions are experimental, not canon.
"""
import argparse,csv,json,random
from pathlib import Path
from founders_civ.core.ledger import Book
from founders_civ.experimental.founders import FounderRegistry
from founders_civ.experimental.soul import AbilityOutcome
from founders_civ.experimental.evolution import Population
from founders_civ.experimental.constructs import ConstructRegistry

def run(seed=42,days=30,shock=True,teaching=True,refuel=True):
    pop=Population(seed=seed,n=30,food_per_patch=240.)
    # Seed all physical accounts in a NEW shared book; never create a second source of truth.
    shared=Book()
    for k,v in pop.book.mass.items(): shared.seed_mass(k,v)
    shared.seed_mass('raw:dimension',10.)
    for k,v in pop.book.energy.items():shared.seed_energy(k,v)
    shared.seed_energy('world_work',100.)
    shared.freeze();pop.book=shared
    founders=FounderRegistry(shared,seed=seed)
    constructs=ConstructRegistry(shared)
    fid='F001';f=founders.people[fid]
    founders.learn(fid,'stewardship',2.,'early ecology practice')
    founders.checkpoint(fid)
    founders.learn(fid,'stewardship',3.,'later field research')
    soul=f.soul
    for node in ('observation','coordination','restoration'):
        for j in range(2):soul.practice(node,f'{seed}:{node}:{j}')
    soul.develop_state('HabitatCare',['observation','coordination'],schema_depth=1.)
    constructs.build('haven','dimension','north','raw:dimension',10.,daily_energy=1.,initial_reserve=3.)
    # Founders and animals are distinct entities; social transmission is between organisms.
    teachers=[x for x in pop.people.values() if x.patch=='north']
    teachers[0].learned_routes.add('route:south')
    for day in range(1,days+1):
        if teaching and day%3==0:
            alive=[x for x in pop.people.values() if x.alive and x.patch=='north']
            carriers=[x for x in alive if 'route:south' in x.learned_routes]
            if carriers:
                for learner in alive[:5]:
                    if learner.id!=carriers[0].id:pop.teach(carriers[0].id,learner.id,'route:south')
        pop.step('cold' if day<=days//2 else 'mild')
        if refuel and day%3==0 and constructs.items['haven'].status=='stable':
            constructs.top_up('haven',3.)
        constructs.tick('haven')
        if day==max(2,days//3) and shock:
            founders.die(fid)
        if day==max(3,days//2) and founders.people[fid].alive:
            founders.checkpoint(fid)
        if day%5==0 and founders.people[fid].alive:
            founders.learn(fid,'stewardship',.25,f'ecological survey day {day}')
            soul=founders.people[fid].soul
            soul.practice('observation',f'survey:{day}')
            if 'HabitatCare' in soul.states:
                soul.activate('HabitatCare',.1,.1,1.,ledger=shared,source='house')
        shared.audit()
    active=[x for x in pop.people.values() if x.alive]
    events=pop.events+founders.events+constructs.events
    return dict(seed=seed,days=days,shock=shock,teaching=teaching,refuel=refuel,
        alive=len(active),births=sum(e['event']=='birth' for e in pop.events),
        deaths=sum(e['event']=='death' for e in pop.events),
        route_knowledge=sum(bool(x.learned_routes) for x in active),
        founder_reborn=any(e['event']=='rebirth' for e in founders.events),
        founder_skill=founders.people[fid].skills.get('stewardship',0.),
        dimension_status=constructs.items['haven'].status,
        dimension_integrity=constructs.items['haven'].integrity,
        soul_states=len(founders.people[fid].soul.states),
        soul_practice_events=len(founders.people[fid].soul.events),
        event_count=len(events),audit=shared.audit())

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--days',type=int,default=30)
    ap.add_argument('--seeds',type=int,default=6);ap.add_argument('--out',default='results/continuity_loop')
    a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    arms={'full':(True,True,True),'no_shock':(False,True,True),'no_teaching':(True,False,True),'no_refuel':(True,True,False)}
    rows=[]
    for seed in range(a.seeds):
        for name,(shock,teaching,refuel) in arms.items():
            r=run(seed=seed+100,days=a.days,shock=shock,teaching=teaching,refuel=refuel)
            r['arm']=name;rows.append(r)
    (out/'results.json').write_text(json.dumps(rows,indent=2))
    fields=[k for k in rows[0] if k!='audit']+['mass_error','energy_error','transactions','toll_events']
    with (out/'results.csv').open('w',newline='') as fh:
        w=csv.DictWriter(fh,fieldnames=fields);w.writeheader()
        for r in rows:w.writerow({**{k:v for k,v in r.items() if k!='audit'},**{k:r['audit'][k] for k in ['mass_error','energy_error','transactions','toll_events']}})
    print(json.dumps({'runs':len(rows),'days':a.days,'max_mass_error':max(abs(r['audit']['mass_error']) for r in rows),'max_energy_error':max(abs(r['audit']['energy_error']) for r in rows),'by_arm':{name:{'alive_mean':round(sum(r['alive'] for r in rows if r['arm']==name)/a.seeds,2),'route_mean':round(sum(r['route_knowledge'] for r in rows if r['arm']==name)/a.seeds,2),'collapsed':sum(r['dimension_status']=='collapsed' for r in rows if r['arm']==name),'reborn':sum(r['founder_reborn'] for r in rows if r['arm']==name)} for name in arms}},indent=2))
if __name__=='__main__':main()
