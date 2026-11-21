import sys,json,hashlib,pickle
sys.path.insert(0,'src')
from integrated_02193 import Unified293
s=Unified293.load('/mnt/data/cycle093/evidence/day30.pkl')
for _ in range(150):s.step()
with open('/mnt/data/cycle093/evidence/day180.pkl','rb') as f:other=pickle.load(f)
def state(x):
 b=x.host.book
 return (x.days,dict(b.mass),dict(b.energy),[(k,v.alive,v.stage,v.generation) for k,v in sorted(x.bridge.actors.items())],x.edible_events)
print(json.dumps({'exact_state_equal':state(s)==state(other),'days':s.days,'events_equal':s.edible_events==other.edible_events}))
