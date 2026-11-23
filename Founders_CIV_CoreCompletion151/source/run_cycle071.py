import json,pickle,sys
from pathlib import Path
from integrated_02170 import Unified270
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
results=[];replay={}
for seed in (9711,9712):
 for enabled in (False,True):
  s=Unified270(seed=seed,resource_access=enabled,capacity_scale=1.0)
  obs={}
  for day in range(1,31):
   s.step()
   if seed==9711 and enabled and day==15:
    (out/'selected_checkpoint.pkl').write_bytes(pickle.dumps(s,pickle.HIGHEST_PROTOCOL))
   if day in (15,30):
    a=s.host.book.audit(); b=s.bridge
    obs[str(day)]={'living':sum(x.alive for x in b.actors.values()),'births':b.stats['birth'],'tree_state':b.tree.state,
      'guided_moves':b.resource_access_metrics['guided_moves'],'unaffordable_moves':b.resource_access_metrics['unaffordable_moves'],
      'mass_error':a['mass_error'],'energy_error':a['energy_error'],'rejections':a.get('rejected',a.get('rejections')),
      'g2_events':sum(e.get('event')=='birth' and e.get('generation',0)>=2 for e in b.events)}
  results.append({'seed':seed,'resource_access':enabled,'observations':obs})
  if seed==9711 and enabled:
   p=pickle.loads((out/'selected_checkpoint.pkl').read_bytes())
   for _ in range(15):p.step()
   replay={'report_equal':p.report()==s.report(),'book_mass_equal':dict(p.host.book.mass)==dict(s.host.book.mass),
           'book_energy_equal':dict(p.host.book.energy)==dict(s.host.book.energy),
           'positions_equal':p.bridge.positions==s.bridge.positions,'events_equal':p.bridge.events==s.bridge.events}
(out/'results.json').write_text(json.dumps(results,indent=2,default=str))
(out/'replay.json').write_text(json.dumps(replay,indent=2))
print(json.dumps({'results':results,'replay':replay}))
