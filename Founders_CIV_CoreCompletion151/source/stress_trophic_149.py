#!/usr/bin/env python3
"""True matched-seed Cycle149 on/off ecological stress; no hidden survival adjustments."""
import argparse,csv,json,sys
from pathlib import Path
from collections import Counter
from trophic_integration_149 import UnifiedTrophicIntegration149
from species_traits_143 import BLUEPRINTS


def capture(sim,seed,enabled,day):
    br=sim.bridge
    alive=Counter(x.species for x in br.actors.values() if x.alive)
    births=Counter(x.species for x in br.actors.values() if x.generation>=2)
    deaths=Counter(e.get('cause','unknown') for e in br.events if e.get('event')=='death')
    killed_by=Counter()
    for e in br.events:
        if e.get('event')=='predation':
            attacker=br.actors.get(e.get('predator'));victim=br.actors.get(e.get('prey'))
            if attacker and victim:killed_by[attacker.species]+=1
    r=dict(seed=seed,enabled=int(enabled),day=day,
        bridge_alive=sum(alive.values()),native_alive=br.tree.population,
        world_state=br.tree.state,g2plus_births=sum(births.values()),
        physiol_deaths=deaths['physiological_failure'],
        killed_by_predation=deaths['predation'],
        kills=br.trophic_metrics.get('successful_kills',0),
        work_unfunded=br.physiology_metrics.get('work_unfunded',0),
        reward_from_prey_reserves=br.integration149_metrics.get('previously_stranded_prey_fuel_to_gut',0),
        preferred_carcass_meals=br.integration149_metrics.get('carcass_preferred_over_kill',0),
        localized_carcass_mass=br.integration149_metrics.get('carcass_mass_localized',0),
        book_rejections=sim.host.book.audit()['rejections'])
    for species in BLUEPRINTS:
        r[f'alive__{species}']=alive[species]
        r[f'g2plus__{species}']=births[species]
        r[f'kills_by__{species}']=killed_by[species]
    return r

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--days',type=int,default=180)
    a.add_argument('--seeds',type=int,nargs='+',default=[100001,100002])
    a.add_argument('--output',default='STRESS149_MATCHED.csv')
    a.add_argument('--snapshot-every',type=int,default=30)
    a.add_argument('--arms',choices=['both','control','candidate'],default='both')
    args=a.parse_args();rows=[]
    for seed in args.seeds:
        for enabled in ((False,True) if args.arms=='both' else (False,) if args.arms=='control' else (True,)):
            sim=UnifiedTrophicIntegration149(seed=seed,trophic_integration=enabled)
            rows.append(capture(sim,seed,enabled,0))
            for day in range(1,args.days+1):
                sim.step()
                if day%args.snapshot_every==0 or day==args.days:
                    row=capture(sim,seed,enabled,day)
                    rows.append(row)
                    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
                    with out.open('w',newline='') as f:
                        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
                    print('seed',seed,'new',enabled,'day',day,
                          'alive',row['bridge_alive'],'hounds',row['alive__ridge_hound'],
                          'foxes',row['alive__red_fox'],'jackals',row['alive__golden_jackal'],
                          'g2',row['g2plus_births'],'kills',row['kills'],
                          'Book reject',row['book_rejections'],flush=True)
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    print('wrote',out)
if __name__=='__main__':main()
