import sys,json,pickle,csv
from pathlib import Path
from integrated_02178 import Unified278
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
rows=[]; replay={}
for seed in (9711,9712):
 for behavior in (False,True):
  for capacity in (0.,.5):
   s=Unified278(seed=seed,unified_behavior=behavior,capacity_scale=capacity)
   snapshots=[]
   for day in range(1,181):
    s.step()
    if day==30 and seed==9711 and behavior and capacity==.5:
     blob=pickle.dumps(s,pickle.HIGHEST_PROTOCOL)
     (out/'selected_checkpoint.pkl').write_bytes(blob)
     replay_s=pickle.loads(blob)
    if day in (30,60,120,180):
     b=s.bridge;au=s.host.book.audit()
     snapshots.append(dict(day=day,living=sum(a.alive for a in b.actors.values()),births=b.stats['birth'],
      g1_adults=sum(a.alive and a.generation>=1 and a.stage=='adult' for a in b.actors.values()),
      g2_births=sum(a.generation>=2 for a in b.actors.values()),tree=b.tree.state,
      mass_error=au['mass_error'],energy_error=au['energy_error'],rejections=au.get('rejections',0)))
   rows.append(dict(seed=seed,behavior=behavior,capacity=capacity,snapshots=snapshots))
   if seed==9711 and behavior and capacity==.5:
    for _ in range(150):replay_s.step()
    def signature(x):
     return (x.report(),dict(x.host.book.mass),dict(x.host.book.energy),
       {k:(a.alive,a.habitat,a.age,a.generation,a.condition) for k,a in x.bridge.actors.items()})
    replay={'exact':signature(s)==signature(replay_s),'day':s.days,'replayed_day':replay_s.days}
   print(seed,behavior,capacity,snapshots[-1],flush=True)
(out/'results.json').write_text(json.dumps(rows,indent=2))
(out/'replay.json').write_text(json.dumps(replay,indent=2))
with (out/'comparison.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['seed','behavior','capacity','day','living','births','g1_adults','g2_births','tree','mass_error','energy_error','rejections']);w.writeheader()
 for r in rows:
  for s in r['snapshots']:w.writerow({**{k:r[k] for k in ('seed','behavior','capacity')},**s})
