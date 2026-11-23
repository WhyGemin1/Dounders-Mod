import argparse,itertools,json,sys,pickle
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES

def run(out,seeds,days):
 with open(out,'w') as f:
  for seed,density,profile,family in itertools.product(seeds,(4,8),('standard','browse_heavy'),(False,True)):
   s=Unified260(seed=seed,counts={k:density*2 for k in SPECIES},capacity_scale=.5,capacity_profile=profile,family_benefits=family,resource_aware_family=family)
   for day in range(1,days+1):
    s.step()
    if day in (30,60,120,180):
     audit=s.host.book.audit();alive=[a for a in s.bridge.actors.values() if a.alive]
     row=dict(seed=seed,density=density,profile=profile,family=family,day=day,living=len(alive),g1_alive=sum(getattr(a,'generation',0)==1 for a in alive),g1_adults=sum(getattr(a,'generation',0)==1 and getattr(a,'age',0)>=getattr(a,'maturity_age',float('inf')) for a in alive),g2_births=sum(getattr(a,'generation',0)>=2 for a in s.bridge.actors.values()),births=s.bridge.stats.get('birth',0),tree=s.bridge.tree.state,mass_error=audit['mass_error'],energy_error=audit['energy_error'],rejections=audit['rejections'])
     assert abs(row['mass_error'])<1e-5 and abs(row['energy_error'])<1e-5 and row['rejections']==0,row
     f.write(json.dumps(row)+'\n');f.flush();print(json.dumps(row),flush=True)
     if seed==9711 and density==4 and profile=='browse_heavy' and family and day==30:
      with open(str(Path(out).parent/'day30_checkpoint.pkl'),'wb') as cp:pickle.dump(s,cp)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--days',type=int,default=60);p.add_argument('--seeds',nargs='+',type=int,default=[9711,9712]);p.add_argument('--out',required=True);a=p.parse_args();run(a.out,a.seeds,a.days)
