"""Cycle110: matched juvenile metabolic conservation vs baseline, fixed funding/family."""
import argparse,json,pickle,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from generation_audit_021108 import generation_metrics

def run(out,seeds=(9711,9712),days=180):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 with (out/'results.jsonl').open('w') as f:
  for seed in seeds:
   for conservation in (False,True):
    s=Unified260(seed=seed,counts={k:8 for k in SPECIES},capacity_scale=.5,family_benefits=True,resource_aware_family=True)
    s.bridge.parental_investment=True;s.bridge.juvenile_energy_conservation=conservation
    start=s.host.sim.tick
    for step in range(1,days+1):
     s.step()
     if step in (30,60,120,180):
      audit=s.host.book.audit();row={'seed':seed,'conservation':conservation,'step':step,'engine_day':s.host.sim.tick,'elapsed':s.host.sim.tick-start,'living':sum(a.alive for a in s.bridge.actors.values()),**generation_metrics(s.bridge),'tree':str(s.bridge.tree.state),'mass_error':audit['mass_error'],'energy_error':audit['energy_error'],'rejections':audit['rejections']}
      assert row['elapsed']==step and abs(row['mass_error'])<1e-5 and abs(row['energy_error'])<1e-5 and row['rejections']==0
      f.write(json.dumps(row)+'\n');f.flush()
      if seed==9711 and conservation and step==30:
       with (out/'day30_checkpoint.pkl').open('wb') as ck:pickle.dump(s,ck)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--days',type=int,default=180);a=p.parse_args();run(a.out,days=a.days)
