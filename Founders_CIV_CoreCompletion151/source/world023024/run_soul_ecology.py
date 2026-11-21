"""Run matched v0.20 ecology / minimal Soul-network test arms."""
import argparse,csv,json
from pathlib import Path
from statistics import mean
from soul_ecology_v021 import EcologyTrial
ARMS=['baseline','episodic','social','full']

def run_batch(seeds=30,steps=12,start_seed=200,with_hazard=True):
    return [EcologyTrial(start_seed+s,arm,hazard=with_hazard).run(steps)
            for s in range(seeds) for arm in ARMS]

def report(rows):
    out={}
    for arm in ARMS:
        group=[r for r in rows if r['arm']==arm]
        out[arm]={k:round(mean(r[k] for r in group),4) for k in
        ['alive','births','deaths','hazard_deaths','migrations','unsafe_exposures',
         'route_carriers','heard','practiced','templates','retrieved','revisions','food_remaining']}
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seeds',type=int,default=30)
    ap.add_argument('--steps',type=int,default=12)
    ap.add_argument('--start-seed',type=int,default=200)
    ap.add_argument('--out',default='results/soul_ecology')
    ap.add_argument('--no-hazard',action='store_true')
    a=ap.parse_args()
    if a.seeds<1 or a.steps<1:ap.error('seeds and steps must be positive')
    rows=run_batch(a.seeds,a.steps,a.start_seed,not a.no_hazard)
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    (out/'results.json').write_text(json.dumps([{k:v for k,v in r.items() if k!='history'} for r in rows],indent=2))
    (out/'summary.json').write_text(json.dumps(report(rows),indent=2))
    with (out/'results.csv').open('w',newline='') as f:
        fields=[k for k in rows[0] if k not in ['audit','history']]
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in rows)
    with (out/'daily.csv').open('w',newline='') as f:
        fields=list(rows[0]['history'][0]);w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in rows:w.writerows(r['history'])
    print(json.dumps({'runs':len(rows),'results':report(rows),
        'max_mass_error':max(abs(r['audit']['mass_error']) for r in rows),
        'max_energy_error':max(abs(r['audit']['energy_error']) for r in rows)},indent=2))
if __name__=='__main__':main()
