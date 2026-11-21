import json,pickle,sys
from pathlib import Path
from integrated_02170 import Unified270
out=Path(sys.argv[1]);out.mkdir(exist_ok=True)
rows=[]
for seed in (9711,9712):
 for enabled in (False,True):
  s=Unified270(seed=seed,resource_access=enabled,capacity_scale=1.)
  for day in range(30):s.step()
  b=s.bridge;au=s.host.book.audit()
  rows.append(dict(seed=seed,resource_access=enabled,days=30,living=sum(a.alive for a in b.actors.values()),births=b.stats['birth'],guided_moves=b.resource_access_metrics['guided_moves'],pressure_opportunities=b.resource_access_metrics['pressure_opportunities'],tree_state=b.tree.state,mass_error=au['mass_error'],energy_error=au['energy_error'],rejections=au.get('rejections',au.get('rejected'))))
  if seed==9711 and enabled:
   (out/'selected_checkpoint.pkl').write_bytes(pickle.dumps(s,pickle.HIGHEST_PROTOCOL))
(out/'results.json').write_text(json.dumps(rows,indent=2,default=str))
print(json.dumps(rows))
