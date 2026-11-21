import sys,json,pickle,csv
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from juvenile_foraging_021114 import enable_juvenile_foraging
from generation_audit_021108 import generation_metrics
out=Path('/mnt/data/cycle115');rows=[]
for seed in (9711,9712):
 for enabled in (False,True):
  s=Unified260(seed=seed,counts={k:8 for k in SPECIES},capacity_scale=.5,family_benefits=True,resource_aware_family=True)
  if enabled:enable_juvenile_foraging(s.bridge)
  start=s.host.sim.tick
  for step in range(1,181):
   s.step()
   if step in (30,60,120,180):
    a=s.host.book.audit();events=getattr(s.bridge,'events',[])
    row=dict(seed=seed,priority=enabled,step=step,day=s.host.sim.tick,living=sum(x.alive for x in s.bridge.actors.values()),tree=str(s.bridge.tree.state),mass_error=a['mass_error'],energy_error=a['energy_error'],rejections=a['rejections'],priority_events=sum(e.get('event')=='juvenile_foraging_priority' for e in events if isinstance(e,dict)),**generation_metrics(s.bridge))
    assert s.host.sim.tick-start==step and a['rejections']==0 and abs(a['mass_error'])<1e-5 and abs(a['energy_error'])<1e-5
    rows.append(row)
    if seed==9711 and enabled and step==30:
     with (out/'day30_checkpoint.pkl').open('wb') as f:pickle.dump(s,f)
  print(seed,enabled,rows[-1]['living'],flush=True)
(out/'results.jsonl').write_text(''.join(json.dumps(r,default=str)+'\n' for r in rows))
with (out/'comparison.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
