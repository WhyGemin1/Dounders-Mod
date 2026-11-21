import json,pickle,sys
from pathlib import Path
from run_cycle107 import snapshot
out=Path(sys.argv[1]);s=pickle.load(open(out/'day30_checkpoint.pkl','rb'));initial=s.host.sim.tick-30
for i in range(150):s.step()
a=snapshot(s,initial,180)
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
fresh=Unified260(seed=9711,counts={k:8 for k in SPECIES},capacity_scale=0,family_benefits=False,resource_aware_family=False)
start=fresh.host.sim.tick
for i in range(180):fresh.step()
b=snapshot(fresh,start,180)
checks={'book_mass':s.host.book.mass==fresh.host.book.mass,'book_energy':s.host.book.energy==fresh.host.book.energy,'actor_states':pickle.dumps(s.bridge.actors)==pickle.dumps(fresh.bridge.actors),'tree_state':(s.bridge.tree.state==fresh.bridge.tree.state and s.bridge.tree.habitats.keys()==fresh.bridge.tree.habitats.keys()),'snapshot':a==b}
result={'checks':checks,'passed':all(checks.values()),'restored':a,'continuous':b}
(out/'replay.json').write_text(json.dumps(result,indent=2,default=str));print(json.dumps(checks));
if not result['passed']:sys.exit(1)
