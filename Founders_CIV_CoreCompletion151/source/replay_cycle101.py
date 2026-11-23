import sys,pickle,json
sys.path.insert(0,'src')
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
s=Unified260(seed=9711,counts={k:8 for k in SPECIES},capacity_scale=.5,family_benefits=True,resource_aware_family=True)
for _ in range(30):s.step()
open('../evidence/day30.pkl','wb').write(pickle.dumps(s,pickle.HIGHEST_PROTOCOL))
t=pickle.loads(open('../evidence/day30.pkl','rb').read())
for _ in range(150):s.step();t.step()
a=s.host.book.audit()
r={'day':s.days,'book_mass':dict(s.host.book.mass)==dict(t.host.book.mass),'book_energy':dict(s.host.book.energy)==dict(t.host.book.energy),'actor_states':pickle.dumps(s.bridge.actors)==pickle.dumps(t.bridge.actors),'tree_state':s.bridge.tree.state==t.bridge.tree.state,'events':s.bridge.events==t.bridge.events,'mass_error':a['mass_error'],'energy_error':a['energy_error'],'rejections':a['rejections']}
open('../evidence/replay.json','w').write(json.dumps(r,indent=2));print(r)
assert all(r[k] for k in ('book_mass','book_energy','actor_states','tree_state','events'))
