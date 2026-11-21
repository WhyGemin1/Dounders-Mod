"""Cycle106 paired 2x2 family-memory x capacity profile screening; no canonical edits."""
import argparse, itertools, json, pickle, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES

def snapshot(s):
 a=s.host.book.audit(); living=[x for x in s.bridge.actors.values() if x.alive]
 return dict(day=s.host.sim.tick,living=len(living),g1_alive=sum(getattr(x,'generation',0)==1 for x in living),g1_adults=sum(getattr(x,'generation',0)==1 and getattr(x,'age',0)>=getattr(x,'maturity_age',float('inf')) for x in living),g2_births=sum(getattr(x,'generation',0)>=2 for x in s.bridge.actors.values()),tree=str(s.bridge.tree.state),mass_error=a['mass_error'],energy_error=a['energy_error'],rejections=a['rejections'])
def run(out,days=30,seeds=(9711,),density=4):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 with (out/'results.jsonl').open('w') as f:
  for seed,profile,family in itertools.product(seeds,('standard','browse_heavy'),(False,True)):
   s=Unified260(seed=seed,counts={k:density*2 for k in SPECIES},capacity_scale=.5,capacity_profile=profile,family_benefits=family,resource_aware_family=family)
   for day in range(1,days+1):
    s.step()
    if day in (30,60,120,180):
     row=dict(seed=seed,density=density,profile=profile,family=family,**snapshot(s))
     assert abs(row['mass_error'])<1e-5 and abs(row['energy_error'])<1e-5 and row['rejections']==0,row
     f.write(json.dumps(row)+'\n');f.flush()
     if seed==seeds[0] and profile=='standard' and not family and day==30:
      with (out/'day30_checkpoint.pkl').open('wb') as ck:pickle.dump(s,ck)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--days',type=int,default=30);p.add_argument('--seeds',nargs='+',type=int,default=[9711]);a=p.parse_args();run(a.out,a.days,a.seeds)
