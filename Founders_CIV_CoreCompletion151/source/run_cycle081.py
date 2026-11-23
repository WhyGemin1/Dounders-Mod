import sys,json,csv,pickle
from pathlib import Path
from integrated_02181 import Unified281
out=Path(sys.argv[1]);out.mkdir(exist_ok=True,parents=True)
rows=[];replay={}
for seed in (9711,9712):
 for intervention in (False,True):
  s=Unified281(seed=seed,reproductive_ecology=True,juvenile_provisioning=intervention,energy_budget=False,unified_behavior=False,capacity_scale=.5)
  shots=[]
  for day in range(1,181):
   s.step()
   if day==30 and seed==9711 and intervention:
    blob=pickle.dumps(s,pickle.HIGHEST_PROTOCOL);(out/'selected_checkpoint.pkl').write_bytes(blob);restored=pickle.loads(blob)
   if day in (30,60,120,180):
    b=s.bridge;au=s.host.book.audit()
    shots.append(dict(day=day,living=sum(a.alive for a in b.actors.values()),births=b.stats['birth'],g1_adults=sum(a.alive and a.generation==1 and a.stage=='adult' for a in b.actors.values()),g2_births=sum(a.generation>=2 for a in b.actors.values()),tree=b.tree.state,mass_error=au['mass_error'],energy_error=au['energy_error'],rejections=au.get('rejections',0)))
  rows.append(dict(seed=seed,intervention=intervention,snapshots=shots))
  if seed==9711 and intervention:
   for _ in range(150):restored.step()
   def sig(x):return (x.report(),dict(x.host.book.mass),dict(x.host.book.energy),{k:(a.alive,a.habitat,a.age,a.generation,a.condition) for k,a in x.bridge.actors.items()})
   replay={'exact':sig(s)==sig(restored),'day':s.days,'replayed_day':restored.days}
  print(seed,intervention,shots[-1],flush=True)
(out/'results.json').write_text(json.dumps(rows,indent=2));(out/'replay.json').write_text(json.dumps(replay,indent=2))
with (out/'comparison.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['seed','intervention','day','living','births','g1_adults','g2_births','tree','mass_error','energy_error','rejections']);w.writeheader()
 for r in rows:
  for s in r['snapshots']:w.writerow({'seed':r['seed'],'intervention':r['intervention'],**s})
