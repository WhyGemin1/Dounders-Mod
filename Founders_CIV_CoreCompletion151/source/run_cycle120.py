import sys,json,csv,pickle
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from interworld_placement_021120 import fund_interworld_placement
from generation_audit_021108 import generation_metrics
out=Path('/mnt/data/cycle120');rows=[]
for seed in (9711,9712):
 for habitat in ('floodplain','grassland'):
  s=Unified260(seed=seed,counts={k:8 for k in SPECIES},capacity_scale=.5,family_benefits=True,resource_aware_family=True)
  receipt=fund_interworld_placement(s.bridge.tree,habitat)
  initial=s.host.sim.tick
  for step in range(1,181):
   s.step()
   if step in (30,60,120,180):
    audit=s.host.book.audit()
    row=dict(seed=seed,placement=habitat,day=step,living=sum(x.alive for x in s.bridge.actors.values()),tree_state=s.bridge.tree.state,book_rejections=audit['rejections'],mass_error=audit['mass_error'],energy_error=audit['energy_error'],**generation_metrics(s.bridge))
    assert s.host.sim.tick-initial==step and audit['rejections']==0 and abs(audit['mass_error'])<1e-5 and abs(audit['energy_error'])<1e-5
    rows.append(row)
    if seed==9711 and habitat=='floodplain' and step==30:
     with (out/'day30_checkpoint.pkl').open('wb') as f:pickle.dump(s,f)
  print(seed,habitat,rows[-1]['living'],flush=True)
(out/'results.jsonl').write_text(''.join(json.dumps(x,default=str)+'\n' for x in rows))
with (out/'comparison.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
