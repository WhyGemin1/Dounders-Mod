import json,pickle,sys
from pathlib import Path
from integrated_02170 import Unified270
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
rows=[];replay={}
for seed in (9711,9712):
 for intervention in (False,True):
  s=Unified270(seed=seed,resource_access=intervention,capacity_scale=1.0)
  snapshots={}
  for day in range(1,181):
   s.step()
   if seed==9711 and intervention and day==30:
    (out/'selected_checkpoint.pkl').write_bytes(pickle.dumps(s,pickle.HIGHEST_PROTOCOL))
   if day in (30,60,120,180):
    b=s.bridge;au=s.host.book.audit()
    snapshots[str(day)]={'living':sum(a.alive for a in b.actors.values()),'births':b.stats['birth'], 'g2_births':sum(e.get('event')=='birth' and e.get('generation',0)>=2 for e in b.events),'tree_state':b.tree.state,'guided_moves':b.resource_access_metrics['guided_moves'],'evaluations':b.resource_access_metrics['evaluations'],'depleted_opportunities':b.resource_access_metrics['depleted_opportunities'],'no_gradient':b.resource_access_metrics['no_gradient'],'mass_error':au['mass_error'],'energy_error':au['energy_error'],'rejections':au.get('rejected',au.get('rejections'))}
  rows.append({'seed':seed,'intervention':intervention,'snapshots':snapshots})
  if seed==9711 and intervention:
   p=pickle.loads((out/'selected_checkpoint.pkl').read_bytes())
   for _ in range(150):p.step()
   replay={'report_equal':p.report()==s.report(),'book_mass_equal':dict(p.host.book.mass)==dict(s.host.book.mass),'book_energy_equal':dict(p.host.book.energy)==dict(s.host.book.energy),'positions_equal':p.bridge.positions==s.bridge.positions,'events_equal':p.bridge.events==s.bridge.events}
(out/'results.json').write_text(json.dumps(rows,indent=2,default=str))
(out/'replay.json').write_text(json.dumps(replay,indent=2))
print(json.dumps({'runs':len(rows),'replay':replay,'day180':[r['snapshots']['180'] for r in rows]}))
