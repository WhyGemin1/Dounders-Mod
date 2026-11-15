import sys,pickle,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from interworld_split_021121 import fund_split_shipment
p=Path('/mnt/data/cycle123/results')
with (p/'seed9711_fraction0.5_day30.pkl').open('rb') as f: restored=pickle.load(f)
with (p/'seed9711_fraction0.5_day180.pkl').open('rb') as f: full=pickle.load(f)
for _ in range(150):restored.step()
def fp(s):
 b=s.host.book
 return dict(tick=s.host.sim.tick,mass=sorted(b.mass.items()),energy=sorted(b.energy.items()),actors=sorted((str(k),a.species,a.age,a.alive,a.habitat,a.parent) for k,a in s.bridge.actors.items()),events=s.bridge.events,tree_state=s.bridge.tree.state,habitats=sorted(s.bridge.tree.habitats))
a,b=fp(restored),fp(full)
r={'passed':a==b,'fields':{k:a[k]==b[k] for k in a},'seed':9711,'fraction':.5,'days':'30+150'}
Path('/mnt/data/cycle123/replay.json').write_text(json.dumps(r,indent=2));print(r)
if not r['passed']:raise SystemExit(1)
