import json,csv,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from river_capacity_021117 import fund_river_floodplain_energy
from generation_audit_021108 import generation_metrics
out=Path('/mnt/data/cycle117');rows=[]
for seed in (9711,9712):
 for enabled in (False,True):
  s=Unified260(seed=seed,counts={k:8 for k in SPECIES},capacity_scale=.5,family_benefits=True,resource_aware_family=True)
  if enabled:fund_river_floodplain_energy(s.bridge.tree,1.0)
  start=s.host.sim.tick
  for step in range(1,61):
   s.step()
   if step in (30,60):
    a=s.host.book.audit()
    r=dict(seed=seed,river_funding=enabled,step=step,living=sum(x.alive for x in s.bridge.actors.values()),tree=s.bridge.tree.state,rejections=a['rejections'],mass_error=a['mass_error'],energy_error=a['energy_error'],**generation_metrics(s.bridge))
    assert s.host.sim.tick-start==step and a['rejections']==0 and abs(a['mass_error'])<1e-5 and abs(a['energy_error'])<1e-5
    rows.append(r)
  print(seed,enabled,rows[-1]['living'],flush=True)
(out/'results.jsonl').write_text(''.join(json.dumps(r,default=str)+'\n' for r in rows))
with (out/'comparison.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
