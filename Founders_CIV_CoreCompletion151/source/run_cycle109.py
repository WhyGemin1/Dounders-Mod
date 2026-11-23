"""Cycle108: clock-correct matched family x capacity 60-step experiment."""
import argparse,json,pickle,sys,itertools
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from generation_audit_021108 import generation_metrics

def snapshot(s,initial_tick,steps):
    audit=s.host.book.audit()
    living=[a for a in s.bridge.actors.values() if a.alive]
    result={'steps':steps,'engine_day':s.host.sim.tick,'initial_engine_day':initial_tick,
      'elapsed_engine_days':s.host.sim.tick-initial_tick,
      'living':len(living),**generation_metrics(s.bridge),
      'tree':str(s.bridge.tree.state),'mass_error':audit['mass_error'],'energy_error':audit['energy_error'],'rejections':audit['rejections']}
    assert result['elapsed_engine_days']==steps, result
    assert abs(result['mass_error'])<1e-5 and abs(result['energy_error'])<1e-5 and result['rejections']==0,result
    return result

def run(out,seeds=(9711,),days=60):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 with (out/'results.jsonl').open('w') as f:
  for seed,capacity,family,investment in itertools.product(seeds,(0,.5),(False,True),(False,True)):
   s=Unified260(seed=seed,counts={k:8 for k in SPECIES},capacity_scale=capacity,family_benefits=family,resource_aware_family=family)
   s.bridge.parental_investment=investment
   initial=s.host.sim.tick
   for step in range(1,days+1):
    s.step()
    if step in (30,60,120,180):
     row={'seed':seed,'capacity':capacity,'family':family,'parental_investment':investment,**snapshot(s,initial,step)}
     f.write(json.dumps(row)+'\n');f.flush()
     if seed==seeds[0] and capacity==0 and not family and step==30:
      with (out/'day30_checkpoint.pkl').open('wb') as ck:pickle.dump(s,ck)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--days',type=int,default=60);a=p.parse_args();run(a.out,days=a.days)
