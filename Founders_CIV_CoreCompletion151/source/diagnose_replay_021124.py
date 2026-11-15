"""Exact replay diagnostic: report first event divergence, never silently normalize."""
import pickle, sys, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from interworld_split_021121 import fund_split_shipment

def build(seed=9711, fraction=.5):
 s=Unified260(seed=seed,counts={k:8 for k in SPECIES},capacity_scale=.5,family_benefits=True,resource_aware_family=True)
 fund_split_shipment(s.bridge.tree,fraction)
 return s

def compare(seed=9711, fraction=.5, days=40, checkpoint_day=30):
 if days<=checkpoint_day:raise ValueError('days must exceed checkpoint')
 full=build(seed,fraction)
 for _ in range(checkpoint_day):full.step()
 resumed=pickle.loads(pickle.dumps(full,protocol=pickle.HIGHEST_PROTOCOL))
 for _ in range(days-checkpoint_day):full.step();resumed.step()
 a,b=full.bridge.events,resumed.bridge.events
 first=next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),None)
 if first is None and len(a)!=len(b):first=min(len(a),len(b))
 booka,bookb=full.host.book,resumed.host.book
 return {'seed':seed,'days':days,'checkpoint_day':checkpoint_day,'events_match':a==b,'events_full':len(a),'events_resumed':len(b),'first_difference':first,'full_event':a[first] if first is not None and first<len(a) else None,'resumed_event':b[first] if first is not None and first<len(b) else None,'book_mass_match':booka.mass==bookb.mass,'book_energy_match':booka.energy==bookb.energy}
if __name__=='__main__':print(json.dumps(compare(),indent=2,default=str))
