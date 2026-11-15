import sys,pickle,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from interworld_placement_021120 import fund_interworld_placement
p=Path('/mnt/data/cycle120')
with (p/'day30_checkpoint.pkl').open('rb') as f:restored=pickle.load(f)
fresh=Unified260(seed=9711,counts={k:8 for k in SPECIES},capacity_scale=.5,family_benefits=True,resource_aware_family=True)
fund_interworld_placement(fresh.bridge.tree,'floodplain')
for _ in range(180):fresh.step()
for _ in range(150):restored.step()
def fingerprint(s):
 b=s.host.book
 return {'tick':s.host.sim.tick,'mass':sorted(b.mass.items()),'energy':sorted(b.energy.items()),'actors':sorted((str(k),a.species,a.age,a.alive,a.habitat,a.parent) for k,a in s.bridge.actors.items()),'events':s.bridge.events,'tree_state':s.bridge.tree.state,'habitats':sorted(s.bridge.tree.habitats)}
a=fingerprint(fresh);b=fingerprint(restored)
parts={k:a[k]==b[k] for k in a};result={'passed':all(parts.values()),'fields':parts,'day':180,'seed':9711,'placement':'floodplain'}
(p/'replay.json').write_text(json.dumps(result,indent=2));print(result)
if not result['passed']:raise SystemExit(1)
