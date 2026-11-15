"""Matched 2x2 ecological stress; continuation of archived Core147 source.

Reuses same seed and initial World stocks for all arms. Logs species-specific
survival and actual descendant recruitment, not only total population.
"""
from __future__ import annotations
import argparse,csv,os,json,sys,time
from collections import Counter
from pathlib import Path
from ecoregulation_148 import UnifiedEcoRegulation148

SPECIES=('field_mouse','meadow_grazer','forest_browser','ridge_hound','carrion_bird',
         'burrow_rabbit','field_vole','ant_colony','insectivore_shrew',
         'red_fox','golden_jackal','forest_elephant','woolly_mammoth')

def run(seed,tracking,mates,days,measure=(30,60,90,120,180,360)):
    sim=UnifiedEcoRegulation148(seed=seed,local_tracking=tracking,mate_search=mates)
    results=[]
    for day in range(1,days+1):
        sim.step()
        if day not in measure and day!=days:continue
        b=sim.bridge
        living=[a for a in b.actors.values() if a.alive]
        counts=Counter(a.species for a in living)
        g2=[a for a in b.actors.values() if a.generation>=2]
        m=b.ecoregulation_metrics
        row=dict(seed=seed,tracking=int(tracking),mate_search=int(mates),day=day,
            alive=len(living),native=sim.bridge.tree.population,world=sim.bridge.tree.state,
            g1_births=sum(a.generation==1 for a in b.actors.values()),
            g2plus_births=len(g2),g2plus_alive=sum(a.alive for a in g2),
            energy_residual=b.book.audit()['energy_error'],
            mass_residual=b.book.audit()['mass_error'],
            book_rejections=b.book.audit()['rejections'],
            physiological_failures=sum(e.get('event')=='death' and e.get('cause')=='physiological_failure'
                for e in getattr(b,'events',[]) if isinstance(e,dict)),
            work_unfunded=b.physiology_metrics['work_unfunded'],
            paid_tracking=m['paid_local_tracking_steps'],
            paid_mate_migrations=m['mate_search_paid_migrations'],
            kills=b.trophic_metrics['successful_kills'])
        for species in SPECIES:
            row['alive__'+species]=counts[species]
            row['g2plus__'+species]=sum(a.species==species for a in g2)
        results.append(row)
    return results

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--seeds',type=int,default=2)
    p.add_argument('--seed-start',type=int,default=100001)
    p.add_argument('--days',type=int,default=120)
    p.add_argument('--out',default='stress148/results.csv')
    args=p.parse_args()
    dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
    rows=[]
    for seed in range(args.seed_start,args.seed_start+args.seeds):
        for tracking,mates in ((False,False),(True,False),(False,True),(True,True)):
            t=time.monotonic()
            result=run(seed,tracking,mates,args.days)
            rows.extend(result)
            with dest.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
            last=result[-1]
            print(json.dumps(dict(seed=seed,track=tracking,mates=mates,day=args.days,
                   alive=last['alive'],hounds=last['alive__ridge_hound'],
                   foxes=last['alive__red_fox'],jackals=last['alive__golden_jackal'],
                   g2=last['g2plus_births'],tracking_steps=last['paid_tracking'],
                   mate_migrations=last['paid_mate_migrations'],
                   book_rejections=last['book_rejections'],elapsed=round(time.monotonic()-t,1))),flush=True)
    print('Wrote',dest,flush=True)
if __name__=='__main__':main()
