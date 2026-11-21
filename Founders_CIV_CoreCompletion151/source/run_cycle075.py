import json,pickle,sys,hashlib
from pathlib import Path
from integrated_02175 import Unified275
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
rows=[];replay={}
for seed in (9711,9712):
 for enabled in (False,True):
  s=Unified275(seed=seed,energy_guard=enabled,adaptive_feeding=False,resource_access=False,capacity_scale=1.)
  snapshots=[]
  for day in range(1,181):
   s.step()
   if day==30 and seed==9711 and enabled:
    blob=pickle.dumps(s,pickle.HIGHEST_PROTOCOL)
    (out/'selected_checkpoint.pkl').write_bytes(blob)
    replay_s=pickle.loads(blob)
   if day in (30,60,120,180):
    b=s.bridge;au=s.host.book.audit()
    snapshots.append(dict(day=day,living=sum(a.alive for a in b.actors.values()),births=b.stats['birth'],tree_state=b.tree.state,ledger=au,guard=dict(b.energy_guard_metrics),mature=sum(a.alive and a.stage=='adult' for a in b.actors.values())))
  rows.append(dict(seed=seed,energy_guard=enabled,snapshots=snapshots))
  if seed==9711 and enabled:
   for _ in range(150):replay_s.step()
   def signature(x):
    return {'report':x.report(),'mass':dict(x.host.book.mass),'energy':dict(x.host.book.energy),'actors':{k:(a.alive,a.habitat,a.age,a.stage,a.condition) for k,a in x.bridge.actors.items()}}
   replay={'exact':signature(s)==signature(replay_s),'day':s.days,'replayed_day':replay_s.days}
(out/'results.json').write_text(json.dumps(rows,indent=2,default=str))
(out/'replay.json').write_text(json.dumps(replay,indent=2))
print(json.dumps({'runs':len(rows),'replay':replay,'endpoints':[(r['seed'],r['energy_guard'],r['snapshots'][-1]['living'],r['snapshots'][-1]['births'],r['snapshots'][-1]['guard'].get('prioritized_feeds',0)) for r in rows]}))
