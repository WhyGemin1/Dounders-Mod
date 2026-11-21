import sys,json,argparse
sys.path.insert(0,'src')
from integrated_02198 import Unified298
from cohort_audit_02197 import cohort_audit
p=argparse.ArgumentParser();p.add_argument('--seed',type=int,default=9711);p.add_argument('--refuge',action='store_true');p.add_argument('--days',type=int,default=180);p.add_argument('--checkpoint');a=p.parse_args()
s=Unified298(seed=a.seed,reproductive_ecology=True,juvenile_foraging=True,capacity_scale=.5,growth_allocation=True,edible_budget=3,scheduled_funding=True,juvenile_refuge=a.refuge)
for _ in range(a.days):
 s.step()
 if s.days==30 and a.checkpoint:s.save(a.checkpoint)
 if s.days in (30,60,120,180):
  c=cohort_audit(s);au=s.host.book.audit()
  print(json.dumps(dict(seed=a.seed,arm='refuge' if a.refuge else 'control',day=s.days,living=sum(x.alive for x in s.bridge.actors.values()),births=s.bridge.stats['birth'],g1_adults=c['g1_adults'],g2_births=c['g2_born'],tree=s.bridge.tree.state,mass_error=au['mass_error'],energy_error=au['energy_error'],rejections=au.get('rejections',0))),flush=True)
