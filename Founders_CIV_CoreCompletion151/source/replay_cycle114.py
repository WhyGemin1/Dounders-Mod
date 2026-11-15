import pickle,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from juvenile_foraging_021114 import enable_juvenile_foraging
p=Path('/mnt/data/cycle114/day30_checkpoint.pkl')
s=Unified260(seed=9711,counts={k:8 for k in SPECIES},capacity_scale=.5,family_benefits=True,resource_aware_family=True)
enable_juvenile_foraging(s.bridge)
for _ in range(30):s.step()
t=pickle.load(p.open('rb'))
for _ in range(150):s.step();t.step()
checks={'mass':s.host.book.mass==t.host.book.mass,'energy':s.host.book.energy==t.host.book.energy,'actors':pickle.dumps(s.bridge.actors)==pickle.dumps(t.bridge.actors),'events':s.bridge.events==t.bridge.events,'clock':s.host.sim.tick==t.host.sim.tick,'tree':s.bridge.tree.state==t.bridge.tree.state}
Path('/mnt/data/cycle114/replay.json').write_text(json.dumps({'checks':checks,'passed':all(checks.values())},indent=2))
assert all(checks.values()),checks
