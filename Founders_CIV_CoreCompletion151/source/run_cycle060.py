import json,pickle,hashlib
from pathlib import Path
from integrated_02160 import Unified260
out=Path('/mnt/data/cycle060/output')
results=[]
for capacity in (0,1):
    s=Unified260(seed=9711,capacity_scale=capacity)
    checkpoints={}
    for day in range(1,181):
        s.step()
        if day in (30,60,120,180):
            r=s.report();c=s.bridge.census()
            checkpoints[day]={'living':r.get('living'), 'tree_state':s.bridge.tree.state,'book':s.host.book.audit(),'generations':s.bridge.spatial_census()['living_generations'],'birth_events':sum(e.get('event')=='birth' for e in s.bridge.events)}
            if day==30 and capacity==1:
                (out/'selected_checkpoint.pkl').write_bytes(pickle.dumps(s,pickle.HIGHEST_PROTOCOL))
    results.append({'seed':9711,'capacity_scale':capacity,'family_benefits':True,'resource_aware_family':True,'checkpoints':checkpoints,'funding':s.capacity_funding})
    if capacity==1:
        replay=pickle.loads((out/'selected_checkpoint.pkl').read_bytes())
        for _ in range(150):replay.step()
        comparison={'report_equal':s.report()==replay.report(),'events_equal':s.bridge.events==replay.bridge.events,'book_mass_equal':dict(s.host.book.mass)==dict(replay.host.book.mass),'book_energy_equal':dict(s.host.book.energy)==dict(replay.host.book.energy),'positions_equal':s.bridge.positions==replay.bridge.positions}
        (out/'replay.json').write_text(json.dumps(comparison,indent=2))
(out/'results.json').write_text(json.dumps(results,indent=2,default=str))
print(json.dumps({'runs':len(results),'day180':[r['checkpoints'][180] for r in results], 'replay':comparison},default=str))
