"""100 preregistered matched WORLD-024 scenario runs; all have 100 Founders."""
import argparse, csv, json, time, traceback
from multiprocessing import Pool
from pathlib import Path
from run_world024_stress import run
DURATIONS=[80,100,120,140,160,180,200,220,260,300]
SEEDS=list(range(820,830))
PROFILES_ORDER=['commons','owner_only','fragmented','unmaintained','extractive','dry_season','disease','upkeep_spike','labor_shock','private_option']
def task(args):
    profile,seed,cycles=args
    try:
        result=run(seed,cycles,profile,captures=(seed==829 and profile in ('commons','unmaintained','private_option')))
        result['test_passed']= (result['founders']==100 and abs(result['conservation']['mass_error'])<1e-5 and abs(result['conservation']['energy_error'])<1e-4)
        result['error']=None
        return result
    except BaseException as exc:
        return dict(profile=profile,seed=seed,duration=cycles,test_passed=False,error=repr(exc),traceback=traceback.format_exc())
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='results/world024/100_stress');ap.add_argument('--workers',type=int,default=4)
    a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    plan=[(p,s,DURATIONS[i]) for p in PROFILES_ORDER for i,s in enumerate(SEEDS)]
    (out/'preregistered_plan.json').write_text(json.dumps(dict(seeds=SEEDS,durations=DURATIONS,profiles=PROFILES_ORDER,scenario_count=len(plan),runs=plan),indent=2))
    start=time.perf_counter(); results=[]
    with (out/'raw_100_runs.jsonl').open('w') as f,Pool(processes=a.workers,maxtasksperchild=4) as pool:
        for k,res in enumerate(pool.imap_unordered(task,plan,chunksize=1),start=1):
            f.write(json.dumps(res)+'\n');f.flush();results.append(res)
            if k%5==0 or not res['test_passed']:
                print('PROGRESS',k,'/100',res.get('profile'),res.get('seed'),res.get('duration'),'passed',res['test_passed'],'state',res.get('shared_tree_state'),'pop',res.get('shared_tree_population'),'elapsed',round(time.perf_counter()-start,1),'s',flush=True)
    results.sort(key=lambda x:(PROFILES_ORDER.index(x['profile']),x['seed']))
    keys=['profile','seed','duration','test_passed','shared_tree_state','shared_tree_population','shared_tree_births','shared_tree_deaths','shared_tree_diseases','shared_tree_plants','tree_collapse_cycle','realm_collapse_cycle','enlisted','distinct_contributors','total_contributions','harvested_mass','eaten_mass','energy_from_tree','private_worlds','private_worlds_active','private_worlds_with_species','post_bootstrap_blueprints','total_food_inventories','house_energy','decisions','events','elapsed_s','error']
    with (out/'100_stress_results.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
        for r in results:w.writerow({k:r.get(k) for k in keys})
    summaries=[]
    for p in PROFILES_ORDER:
        rr=[r for r in results if r['profile']==p]; ok=[r for r in rr if r['test_passed']]
        def avg(key):return round(sum(x.get(key,0) for x in ok)/len(ok),4) if ok else None
        collapses=[x['tree_collapse_cycle'] for x in ok if x.get('tree_collapse_cycle') is not None]
        summaries.append(dict(profile=p,run_count=len(rr),passed=len(ok),tree_alive_at_end=sum(x.get('shared_tree_state')=='active' for x in ok),mean_final_population=avg('shared_tree_population'),mean_collapse_cycle=round(sum(collapses)/len(collapses),2) if collapses else None,mean_enlisted=avg('enlisted'),mean_contributors=avg('distinct_contributors'),mean_harvest_mass=avg('harvested_mass'),mean_food_energy=avg('energy_from_tree'),mean_private_worlds=avg('private_worlds')))
    result=dict(total_runs=len(results),passed=sum(x['test_passed'] for x in results),failed=sum(not x['test_passed'] for x in results),duration_sum=sum(x['duration'] for x in results),founder_decision_opportunities=sum(x.get('decisions',0) for x in results),run_elapsed_s=round(time.perf_counter()-start,2),profiles=summaries,exceptions=[x for x in results if not x['test_passed']])
    (out/'100_stress_summary.json').write_text(json.dumps(result,indent=2))
    print('FINISHED',json.dumps({k:v for k,v in result.items() if k!='profiles'}),flush=True)
    for p in summaries:print('PROFILE',json.dumps(p),flush=True)
if __name__=='__main__':main()
