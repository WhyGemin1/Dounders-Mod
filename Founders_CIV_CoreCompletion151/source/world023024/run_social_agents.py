"""Seed-matched social-agent experiment suite, Python standard library only.

Usage: python run_social_agents.py --seeds 25 --ticks 30 --out results/social_25
"""
from __future__ import annotations
import argparse,csv,json,math,os
from collections import defaultdict
from random import Random
from statistics import mean, stdev
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from founders_civ.experimental.social_agents import SocialSimulation

ARMS=['full','no_partner','no_teach','no_faction','neutral_trust','isolated']
METRICS=['factions','faction_members','cross_squad_factions','informed',
         'multi_exposed','knowledge_events','cross_squad_teach_events',
         'mean_partner_benevolence_trust','mean_total_skill',
         'high_ambition_skill_gain','low_ambition_skill_gain',
         'promises_fulfilled','promises_unfulfilled']


def paired_ci(deltas,seed=123,replicates=2000):
    rg=Random(seed)
    n=len(deltas)
    xs=sorted(mean(deltas[rg.randrange(n)] for _ in range(n)) for j in range(replicates))
    return [round(xs[int(.025*(replicates-1))],5),round(xs[int(.975*(replicates-1))],5)]


def simulate_seed(seed,ticks,start_seed):
    rows=[];demo=None
    for arm in ARMS:
        sim=SocialSimulation(seed,arm,capture=(seed==start_seed and arm=='full'))
        report=sim.run(ticks)
        row={'seed':seed,'arm':arm,'ticks':ticks,
             **{k:report[k] for k in METRICS},
             **{f'action_{k}':v for k,v in report['actions'].items()},
             'energy_error':report['energy_mass_audit']['energy_error'],
             'mass_error':report['energy_mass_audit']['mass_error']}
        rows.append(row)
        if seed==start_seed and arm=='full':
            demo={'seed':seed,'mode':arm,'observations':sim.observations,
                  'events':sim.events,'summary':report}
    return rows,demo

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--seeds',type=int,default=25)
    ap.add_argument('--start-seed',type=int,default=400)
    ap.add_argument('--ticks',type=int,default=30)
    ap.add_argument('--out',default='results/social_agents_25')
    ap.add_argument('--workers',type=int,default=4)
    args=ap.parse_args()
    if args.seeds<1 or args.ticks<1:ap.error('seeds and ticks must be positive')
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    rows=[];demo=None
    if args.workers<=1:
        for seed in range(args.start_seed,args.start_seed+args.seeds):
            rr,dd=simulate_seed(seed,args.ticks,args.start_seed)
            rows.extend(rr);demo=dd or demo
            print(f'Seed {seed} completed all {len(ARMS)} arms',flush=True)
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures={executor.submit(simulate_seed,seed,args.ticks,args.start_seed):seed
                     for seed in range(args.start_seed,args.start_seed+args.seeds)}
            for future in as_completed(futures):
                rr,dd=future.result()
                rows.extend(rr);demo=dd or demo
                print(f'Seed {futures[future]} completed all {len(ARMS)} arms',flush=True)
    rows.sort(key=lambda row:(row['seed'],ARMS.index(row['arm'])))
    columns=['seed','arm','ticks']+METRICS+sorted({k for r in rows for k in r if k.startswith('action_')})+['energy_error','mass_error']
    with open(out/'runs.csv','w',newline='',encoding='utf8') as f:
        writer=csv.DictWriter(f,columns);writer.writeheader();writer.writerows(rows)
    byarm=defaultdict(list)
    for row in rows:byarm[row['arm']].append(row)
    summary={}
    for arm,v in byarm.items():
        summary[arm]={k:{'mean':round(mean(r[k] for r in v),5),
                         'sd':round(stdev(r[k] for r in v),5) if len(v)>1 else 0.0}
                      for k in METRICS}
        summary[arm]['decision_actions_mean']=round(mean(r.get('action_decision',0) for r in v),4)
        summary[arm]['teaching_actions_mean']=round(mean(r.get('action_teach',0) for r in v),4)
        summary[arm]['aid_actions_mean']=round(mean(r.get('action_aid',0) for r in v),4)
    byseed={(r['seed'],r['arm']):r for r in rows}
    contrasts={}
    for arm in ARMS[1:]:
        contrasts[arm]={}
        for k in METRICS:
            d=[byseed[(seed,'full')][k]-byseed[(seed,arm)][k]
               for seed in range(args.start_seed,args.start_seed+args.seeds)]
            contrasts[arm][k]={'full_minus_control':round(mean(d),5),
                               'paired_95pct_bootstrap_ci':paired_ci(d,seed=123+len(k)+len(arm))}
    report={'interpretation':'Synthetic experimental policy comparison, not human data; intervention policies differ in action opportunities. Not a full core.engine.Simulation.step integration.',
            'seeds':list(range(args.start_seed,args.start_seed+args.seeds)),
            'ticks':args.ticks,'founders_per_run':100,'arms':ARMS,
            'runs':len(rows),'summary':summary,'paired_contrasts':contrasts,
            'tests':{'conservation_pass':all(abs(r['mass_error'])<1e-7 and abs(r['energy_error'])<1e-7 for r in rows)}}
    (out/'summary.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    (out/'demo_observatory.json').write_text(json.dumps(demo,separators=(',',':')),encoding='utf8')
    with open(out/'sample_events.jsonl','w',encoding='utf8') as f:
        for e in demo['events']:f.write(json.dumps(e)+'\n')
    print('RESULTS',json.dumps({'runs':len(rows),'tests':report['tests'],
          'full':{k:summary['full'][k]['mean'] for k in ('factions','faction_members','informed','cross_squad_factions')},
          'paired':{k:contrasts[k]['informed']['full_minus_control'] for k in contrasts}},indent=2),flush=True)

if __name__=='__main__':main()
