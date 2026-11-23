"""Matched seed trials, no forced species persistence. Re-run on desktop for longer windows."""
import argparse,csv,os,sys,time
from collections import Counter
from core_completion_146 import UnifiedCoreCompletion146
from trophic_guilds_cycle138 import GUILD_FOUNDERS
from habitat_bridge import SPECIES

ARM={'baseline':(False,False,False),'diet':(True,False,False),
     'hunting':(False,True,False),'combined':(True,True,True)}
SPECIES_ALL=tuple(SPECIES)+tuple(GUILD_FOUNDERS)

def snap(sim,seed,arm):
    b=sim.bridge;live=Counter(a.species for a in b.actors.values() if a.alive)
    birth=Counter(a.species for a in b.actors.values() if a.generation>=2)
    metrics=b.trophic_metrics;stats=sim.host.book.audit()
    row={'seed':seed,'arm':arm,'day':sim.days,'world':b.tree.state,
         'bridge_alive':sum(live.values()),'native_alive':b.tree.population,
         'g2_births':sum(a.generation==2 for a in b.actors.values()),
         'g3plus_births':sum(a.generation>=3 for a in b.actors.values()),
         'kills':metrics['successful_kills'],'scavenge_meals':metrics['scavenge_meals'],
         'book_rejections':stats['rejections'],
         'energy_error':stats['energy_error'],'mass_error':stats['mass_error'],
         'book_transactions':stats['transactions']}
    for sp in SPECIES_ALL:
        row['alive_'+sp]=live[sp];row['g2plus_'+sp]=birth[sp]
    return row

def run(seed,arm,days,interval):
    diet,hunt,care=ARM[arm]
    sim=UnifiedCoreCompletion146(seed=seed,trophic_diet=diet,
                                 trophic_hunting=hunt,trophic_provisioning=care)
    out=[snap(sim,seed,arm)]
    for target in sorted(set(range(interval,days+1,interval))|{days}):
        sim.run(target-sim.days)
        out.append(snap(sim,seed,arm))
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--days',type=int,default=180)
    p.add_argument('--seeds',default='100001,100002')
    p.add_argument('--arms',default='baseline,diet,hunting,combined')
    p.add_argument('--interval',type=int,default=30)
    p.add_argument('--output',default='cycle146_comparison.csv')
    args=p.parse_args()
    os.makedirs(os.path.dirname(args.output) or '.',exist_ok=True)
    with open(args.output,'w',newline='') as f:
        writer=None
        for seed in map(int,args.seeds.split(',')):
            for arm in args.arms.split(','):
                started=time.monotonic()
                rows=run(seed,arm,args.days,args.interval)
                if writer is None:
                    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader()
                writer.writerows(rows);f.flush()
                end=rows[-1]
                print(f'Seed {seed}, {arm}, day {args.days}: '
                      f"alive={end['bridge_alive']} hounds={end['alive_ridge_hound']} "
                      f"fox={end['alive_red_fox']} jackal={end['alive_golden_jackal']} "
                      f"rabbits={end['alive_burrow_rabbit']} G2={end['g2_births']} "
                      f"native={end['native_alive']} world={end['world']} "
                      f"reject={end['book_rejections']} seconds={time.monotonic()-started:.1f}",flush=True)
