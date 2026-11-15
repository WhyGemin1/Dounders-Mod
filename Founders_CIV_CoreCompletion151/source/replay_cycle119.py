import sys,json,pickle,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from interworld_capacity_021119 import fund_interworld_floodplain
out=Path('/mnt/data/cycle119')
def digest(s):
 b=s.host.book
 x={'tick':s.host.sim.tick,'mass':sorted(b.mass.items()),'energy':sorted(b.energy.items()),'animals':sorted((k,repr(vars(v))) for k,v in s.bridge.actors.items()),'tree':s.bridge.tree.state,'habitats':sorted(s.bridge.tree.habitats),'events':repr(s.bridge.events) if hasattr(s.bridge,'events') else None}
 return hashlib.sha256(repr(x).encode()).hexdigest()
s=Unified260(seed=9711,counts={k:8 for k in SPECIES},capacity_scale=.5,family_benefits=True,resource_aware_family=True)
fund_interworld_floodplain(s.bridge.tree)
for _ in range(180):s.step()
expected=digest(s)
with (out/'day30_checkpoint.pkl').open('rb') as f:r=pickle.load(f)
for _ in range(150):r.step()
actual=digest(r)
result={'exact_30_plus_150':expected==actual,'expected_sha256':expected,'actual_sha256':actual,'book_audit':r.host.book.audit(),'living':sum(x.alive for x in r.bridge.actors.values())}
(out/'replay.json').write_text(json.dumps(result,indent=2,default=str))
assert expected==actual
print('REPLAY PASSED',actual)
