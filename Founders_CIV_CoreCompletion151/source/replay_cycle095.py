import sys,json,os,tempfile,pickle
sys.path.insert(0,'src')
from integrated_02195 import Unified295
args=dict(seed=9711,reproductive_ecology=True,juvenile_foraging=True,capacity_scale=.5,growth_allocation=True,edible_budget=3,scheduled_funding=True,funded_access=True)
a=Unified295(**args)
for _ in range(180):a.step()
b=Unified295(**args)
for _ in range(30):b.step()
path='../evidence/day30.pkl';b.save(path)
c=Unified295.load(path)
for _ in range(150):c.step()
keys=lambda s:(s.host.book.mass,s.host.book.energy,[(x.id,x.alive,x.habitat,x.age,x.generation,x.stage) for x in s.bridge.actors.values()],s.edible_events,s.access_snapshots)
result={'exact':keys(a)==keys(c),'day':c.days,'book_equal':a.host.book.mass==c.host.book.mass and a.host.book.energy==c.host.book.energy}
print(json.dumps(result));assert result['exact']
