import sys,json
sys.path.insert(0,'src')
from integrated_02198 import Unified298
kwargs=dict(seed=9711,reproductive_ecology=True,juvenile_foraging=True,capacity_scale=.5,growth_allocation=True,edible_budget=3,scheduled_funding=True,juvenile_refuge=True)
a=Unified298(**kwargs)
for _ in range(180):a.step()
b=Unified298.load('/mnt/data/cycle098/day30_9711_refuge.pkl')
for _ in range(150):b.step()
def state(s):
 return (s.days,dict(s.host.book.mass),dict(s.host.book.energy),[(k,v.alive,v.stage,v.generation,v.habitat,v.age) for k,v in sorted(s.bridge.actors.items())],s.edible_events,s.access_snapshots)
print(json.dumps(dict(exact_state_equal=state(a)==state(b),days=a.days)))
