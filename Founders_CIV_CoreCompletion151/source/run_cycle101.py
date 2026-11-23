"""Cycle101 matched factorial: density x finite capacity x RSW-K family memory."""
import argparse,csv,itertools,json,pickle,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES

def run(seeds=(9711,9712),days=60,out='cycle101_results.jsonl'):
    path=Path(out);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w') as f:
      for seed,density,capacity,family in itertools.product(seeds,(4,8),(0.0,0.5),(False,True)):
        s=Unified260(seed=seed,counts={k:density*2 for k in SPECIES},capacity_scale=capacity,family_benefits=family,resource_aware_family=family)
        for day in range(1,days+1):
          s.step()
          if day in (30,60,120,180):
            audit=s.host.book.audit();spatial=s.bridge.spatial_census()
            row=dict(seed=seed,density_pairs=density,capacity_scale=capacity,family=family,day=day,living=sum(x.alive for x in s.bridge.actors.values()),births=s.bridge.stats.get('birth',0),tree=s.bridge.tree.state,capacity_funding=s.capacity_funding,mass_error=audit['mass_error'],energy_error=audit['energy_error'],rejections=audit['rejections'],living_generations=spatial.get('living_generations'))
            assert abs(row['mass_error'])<1e-5 and abs(row['energy_error'])<1e-5 and row['rejections']==0,row
            f.write(json.dumps(row,default=str)+'\n');f.flush()
            print(json.dumps({k:row[k] for k in ('seed','density_pairs','capacity_scale','family','day','living','births')}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--days',type=int,default=60);p.add_argument('--seeds',nargs='+',type=int,default=[9711,9712]);p.add_argument('--out',default='cycle101_results.jsonl');a=p.parse_args();run(a.seeds,a.days,a.out)
