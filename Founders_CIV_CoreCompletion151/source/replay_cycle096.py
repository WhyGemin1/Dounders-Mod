import sys,json
sys.path.insert(0,'src')
from integrated_02196 import Unified296
kwargs=dict(seed=9711,reproductive_ecology=True,juvenile_foraging=True,capacity_scale=.5,growth_allocation=True,edible_budget=3,scheduled_funding=True,conservative_access=True)
a=Unified296(**kwargs)
for _ in range(180):a.step()
b=Unified296.load('../evidence/day30_9711_conservative.pkl')
for _ in range(150):b.step()
def state(s):
 return (s.days,dict(s.host.book.mass),dict(s.host.book.energy),[(k,v.alive,v.stage,v.generation,v.habitat) for k,v in sorted(s.bridge.actors.items())],s.edible_events,s.access_snapshots)
print(json.dumps({'exact_state_equal':state(a)==state(b),'days':a.days,'events_equal':a.edible_events==b.edible_events}))
