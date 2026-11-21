import json,sys,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from generation_audit_021108 import generation_metrics
from juvenile_dispatch_021111 import enable_juvenile_conservation
p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--days',type=int,default=60);args=p.parse_args()
out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
with (out/'results.jsonl').open('w') as f:
 for seed in (9711,9712):
  for treatment in (False,True):
   s=Unified260(seed=seed,counts={k:8 for k in SPECIES},capacity_scale=.5,family_benefits=True,resource_aware_family=True)
   if treatment:enable_juvenile_conservation(s.bridge)
   start=s.host.sim.tick
   for step in range(1,args.days+1):
    s.step()
    if step in (30,60,120,180):
     audit=s.host.book.audit()
     row={'seed':seed,'treatment':treatment,'step':step,'elapsed':s.host.sim.tick-start,'living':sum(a.alive for a in s.bridge.actors.values()),**generation_metrics(s.bridge),'tree':s.bridge.tree.state,'mass_error':audit['mass_error'],'energy_error':audit['energy_error'],'rejections':audit['rejections']}
     assert row['elapsed']==step and abs(row['mass_error'])<1e-5 and abs(row['energy_error'])<1e-5 and row['rejections']==0
     f.write(json.dumps(row,default=str)+'\n');f.flush()
