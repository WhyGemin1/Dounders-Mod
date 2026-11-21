import argparse,json,csv
from pathlib import Path
from unified_02113 import Unified213
p=argparse.ArgumentParser();p.add_argument('--seeds',default='9711,9712');p.add_argument('--days',type=int,default=30);p.add_argument('--governance',default='collective');p.add_argument('--out',default='results/batch');a=p.parse_args()
out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
for seed in map(int,a.seeds.split(',')):
    target=out/f'{seed}_{a.governance}.json'
    if target.exists():continue
    sim=Unified213(seed=seed,governance=a.governance)
    result=sim.run(a.days)
    target.write_text(json.dumps(result,indent=2))
    sim.save(out/f'{seed}_{a.governance}.pkl')
    print(seed,result['species'],result['tree_state'])
