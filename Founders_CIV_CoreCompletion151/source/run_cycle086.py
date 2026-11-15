import sys,json
sys.path.insert(0,'src')
from integrated_02186 import Unified286
for seed in (9711,9712):
 for enabled in (False,True):
  s=Unified286(seed=seed,reproductive_ecology=True,juvenile_foraging=True,natal_foraging=False,lactation_growth=False,energy_budget=False,unified_behavior=False,capacity_scale=.5,compensatory_grazing=False,maturation_feeding=enabled)
  for i in range(180):s.step()
  b=s.bridge; au=s.host.book.audit()
  print(json.dumps(dict(seed=seed,enabled=enabled,days=s.days,living=sum(a.alive for a in b.actors.values()),births=b.stats['birth'],g1_adults=sum(a.alive and a.generation==1 and a.stage=='adult' for a in b.actors.values()),g2_births=sum(a.generation>=2 for a in b.actors.values()),tree=b.tree.state,mass_error=au['mass_error'],energy_error=au['energy_error'],rejections=au.get('rejections',0))),flush=True)
