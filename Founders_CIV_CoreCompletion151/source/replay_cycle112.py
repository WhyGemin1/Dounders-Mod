import pickle,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from juvenile_dispatch_021111 import enable_juvenile_conservation
out=Path('/mnt/data/cycle112')
def make():
 s=Unified260(seed=9712,counts={k:8 for k in SPECIES},capacity_scale=.5,family_benefits=True,resource_aware_family=True)
 enable_juvenile_conservation(s.bridge)
 return s
s=make()
for _ in range(30):s.step()
with (out/'day30_checkpoint.pkl').open('wb') as f:pickle.dump(s,f,pickle.HIGHEST_PROTOCOL)
t=pickle.load((out/'day30_checkpoint.pkl').open('rb'))
for _ in range(150):s.step();t.step()
checks={'book_mass':s.host.book.mass==t.host.book.mass,'book_energy':s.host.book.energy==t.host.book.energy,'actors':pickle.dumps(s.bridge.actors)==pickle.dumps(t.bridge.actors),'tree':(s.bridge.tree.state==t.bridge.tree.state and list(s.bridge.tree.habitats)==list(t.bridge.tree.habitats)),'events':s.bridge.events==t.bridge.events,'clock':s.host.sim.tick==t.host.sim.tick}
(out/'replay.json').write_text(json.dumps({'checks':checks,'passed':all(checks.values())},indent=2))
assert all(checks.values()),checks
