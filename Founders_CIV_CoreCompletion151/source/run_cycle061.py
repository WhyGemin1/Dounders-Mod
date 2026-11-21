import json,pickle,csv
from pathlib import Path
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
out=Path('output');out.mkdir(exist_ok=True)
rows=[]; replay=None
for seed in (9711,):
 for density in (4,):
  for capacity in (0,1):
   for family in (False,True):
    s=Unified260(seed=seed,counts={k:density*2 for k in SPECIES},capacity_scale=capacity,family_benefits=family,resource_aware_family=family)
    saved=None
    for day in range(1,31):
     s.step()
     if day==15 and seed==9711 and density==4 and capacity==1 and family:
      saved=pickle.dumps(s,pickle.HIGHEST_PROTOCOL);(out/'Cycle061_day30_checkpoint.pkl').write_bytes(saved)
    r=s.report(); a=s.host.book.audit(); spatial=s.bridge.spatial_census()
    rows.append(dict(seed=seed,density_pairs=density,capacity=capacity,family=family,day=30,living=r.get('living'),tree_state=s.bridge.tree.state,birth_events=sum(e.get('event')=='birth' for e in s.bridge.events),living_generations=str(spatial.get('living_generations')),rejections=a['rejections'],mass_error=a['mass_error'],energy_error=a['energy_error']))
    if saved:
     b=pickle.loads(saved)
     for _ in range(15):b.step()
     replay=dict(report=s.report()==b.report(),events=s.bridge.events==b.bridge.events,book_mass=dict(s.host.book.mass)==dict(b.host.book.mass),book_energy=dict(s.host.book.energy)==dict(b.host.book.energy),positions=s.bridge.positions==b.bridge.positions)
with (out/'Cycle061_comparison.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(out/'Cycle061_results.json').write_text(json.dumps(rows,indent=2))
(out/'Cycle061_replay.json').write_text(json.dumps(replay,indent=2))
print(json.dumps({'runs':len(rows),'replay':replay,'rows':rows},default=str))
