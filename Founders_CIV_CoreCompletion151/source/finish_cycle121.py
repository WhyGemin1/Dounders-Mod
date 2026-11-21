import sys,pickle,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from interworld_split_021121 import fund_split_shipment
from generation_audit_021108 import generation_metrics
p=Path('/mnt/data/cycle121');s=Unified260(seed=9711,counts={k:8 for k in SPECIES},capacity_scale=.5,family_benefits=True,resource_aware_family=True);fund_split_shipment(s.bridge.tree,.5)
with (p/'day30_checkpoint.pkl').open('rb') as f:restored=pickle.load(f)
for _ in range(180):s.step()
for _ in range(150):restored.step()
def fingerprint(x):
 b=x.host.book
 return {'tick':x.host.sim.tick,'mass':sorted(b.mass.items()),'energy':sorted(b.energy.items()),'actors':sorted((str(k),a.species,a.age,a.alive,a.habitat,a.parent) for k,a in x.bridge.actors.items()),'events':x.bridge.events,'tree_state':x.bridge.tree.state,'habitats':sorted(x.bridge.tree.habitats)}
a=fingerprint(s);b=fingerprint(restored);fields={k:a[k]==b[k] for k in a};result={'passed':all(fields.values()),'fields':fields,'seed':9711,'fraction':.5,'day':180,'metrics':generation_metrics(s.bridge)}
(p/'replay.json').write_text(json.dumps(result,indent=2,default=str));print(result)
