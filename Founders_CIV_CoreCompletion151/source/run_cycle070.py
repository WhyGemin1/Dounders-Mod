import json,pickle,sys
from pathlib import Path
from integrated_02170 import Unified270
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
results=[];replay=None
for seed in (9711,):
 for enabled in (False,True):
  s=Unified270(seed=seed,resource_access=enabled,capacity_scale=1.0)
  observations={}
  for day in range(1,31):
   s.step()
   if day in (15,30):
    r=s.report();audit=s.host.book.audit()
    observations[str(day)]={'living':sum(a.alive for a in s.bridge.actors.values()),'tree_state':s.bridge.tree.state,'births':s.bridge.stats['birth'],
      'g2_births':sum(e.get('event')=='birth' and e.get('generation',0)>=2 for e in s.bridge.events),
      'guided_moves':s.bridge.resource_access_metrics['guided_moves'],
      'mass_error':audit['mass_error'],'energy_error':audit['energy_error'],
      'rejections':audit.get('rejected',audit.get('rejections',None))}
   if seed==9711 and enabled and day==15:
    (out/'selected_checkpoint.pkl').write_bytes(pickle.dumps(s,pickle.HIGHEST_PROTOCOL))
  results.append({'seed':seed,'resource_access':enabled,'observations':observations})
  if seed==9711 and enabled:
   p=pickle.loads((out/'selected_checkpoint.pkl').read_bytes())
   for _ in range(15):p.step()
   replay={'report_equal':p.report()==s.report(),'book_mass_equal':dict(p.host.book.mass)==dict(s.host.book.mass),
           'book_energy_equal':dict(p.host.book.energy)==dict(s.host.book.energy),
           'positions_equal':p.bridge.positions==s.bridge.positions,'events_equal':p.bridge.events==s.bridge.events}
(out/'results.json').write_text(json.dumps(results,indent=2,default=str))
(out/'replay.json').write_text(json.dumps(replay,indent=2))
print(json.dumps({'results':results,'replay':replay}))
