"""Matched 2x2x2 experimental combinations; no canonical edits."""
import argparse,itertools,json,sys
sys.path.insert(0,'src')
from integrated_02198 import Unified298
from cohort_audit_02197 import cohort_audit
p=argparse.ArgumentParser();p.add_argument('--seeds',nargs='+',type=int,default=[9711,9712]);p.add_argument('--days',type=int,default=60);p.add_argument('--output',default='cycle100_results.jsonl');a=p.parse_args()
with open(a.output,'w') as f:
 for seed in a.seeds:
  for nutrition,capacity,refuge in itertools.product((False,True),repeat=3):
   params=dict(reproductive_ecology=True,juvenile_foraging=True,capacity_scale=.5,growth_allocation=True,edible_budget=3,maturation_feeding=nutrition,dependent_nutrition=nutrition,scheduled_funding=capacity,juvenile_refuge=refuge)
   s=Unified298(seed=seed,**params)
   for _ in range(a.days):
    s.step()
    if s.days in (30,60,120,180):
     audit=s.host.book.audit();cohort=cohort_audit(s)
     row=dict(seed=seed,nutrition=nutrition,capacity=capacity,refuge=refuge,day=s.days,living=sum(x.alive for x in s.bridge.actors.values()),births=s.bridge.stats['birth'],g1_adults=cohort['g1_adults'],g2_births=cohort['g2_born'],tree=s.bridge.tree.state,mass_error=audit['mass_error'],energy_error=audit['energy_error'],rejections=audit.get('rejections',0))
     assert abs(row['mass_error'])<1e-5 and abs(row['energy_error'])<1e-5 and row['rejections']==0,row
     f.write(json.dumps(row)+'\n');f.flush();print(json.dumps(row),flush=True)
