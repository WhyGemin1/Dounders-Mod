import sys,json,pickle
from pathlib import Path
from integrated_02177 import Unified277
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
rows=[];replay={}
for seed in (9711,9712):
 for enabled in (False,True):
  s=Unified277(seed=seed,mortality_audit=enabled,energy_path_audit=False,energy_guard=False,adaptive_feeding=False,resource_access=False,capacity_scale=1.)
  snapshots=[]
  for day in range(1,181):
   s.step()
   if day==30 and seed==9711 and enabled:
    blob=pickle.dumps(s,pickle.HIGHEST_PROTOCOL);(out/'selected_checkpoint.pkl').write_bytes(blob)
    resumed=pickle.loads(blob)
   if day in (30,60,120,180):
    b=s.bridge
    snapshots.append(dict(day=day,living=sum(a.alive for a in b.actors.values()),births=b.stats['birth'],tree_state=b.tree.state,ledger=s.host.book.audit(),mortality=dict(b.mortality_metrics) if enabled else {},g1_adults=sum(a.alive and a.stage=='adult' for a in b.actors.values()),g2_births=b.stats.get('g2_birth',0)))
  rows.append(dict(seed=seed,mortality_audit=enabled,snapshots=snapshots))
  if seed==9711 and enabled:
   for _ in range(150):resumed.step()
   def signature(x):
    return dict(report=x.report(),mass=dict(x.host.book.mass),energy=dict(x.host.book.energy),actors={k:(a.alive,a.habitat,a.age,a.stage,a.condition) for k,a in x.bridge.actors.items()})
   replay=dict(exact=signature(s)==signature(resumed),day=s.days,resumed_day=resumed.days)
(out/'results.json').write_text(json.dumps(rows,indent=2,default=str));(out/'replay.json').write_text(json.dumps(replay,indent=2))
print(json.dumps({'runs':len(rows),'replay':replay,'day180':[(r['seed'],r['mortality_audit'],r['snapshots'][-1]['living'],r['snapshots'][-1]['births'],r['snapshots'][-1]['mortality']) for r in rows]}))
