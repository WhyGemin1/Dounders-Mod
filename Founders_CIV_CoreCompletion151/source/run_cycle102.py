"""Matched profile x family factorial; finite debits, no demographic scheduler changes."""
import argparse,itertools,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES

def run(seeds,days,out):
 with open(out,'w') as f:
  for seed,profile,family in itertools.product(seeds,('standard','forage_priority'),(False,True)):
   s=Unified260(seed=seed,counts={k:8 for k in SPECIES},capacity_scale=.5,capacity_profile=profile,family_benefits=family,resource_aware_family=family)
   for day in range(1,days+1):
    s.step()
    if day in (30,60,120,180):
     audit=s.host.book.audit();alive=[x for x in s.bridge.actors.values() if x.alive]
     row=dict(seed=seed,profile=profile,family=family,day=day,living=len(alive),births=s.bridge.stats.get('birth',0),g1_alive=sum(getattr(x,'generation',0)==1 for x in alive),tree=s.bridge.tree.state,mass_error=audit['mass_error'],energy_error=audit['energy_error'],rejections=audit['rejections'],funding=s.capacity_funding)
     assert abs(row['mass_error'])<1e-5 and abs(row['energy_error'])<1e-5 and row['rejections']==0,row
     f.write(json.dumps(row,default=str)+'\n');f.flush();print(json.dumps({k:row[k] for k in ('seed','profile','family','day','living','births')}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--days',type=int,default=60);p.add_argument('--seeds',nargs='+',type=int,default=[9711,9712]);p.add_argument('--out',default='results.jsonl');a=p.parse_args();run(a.seeds,a.days,a.out)
