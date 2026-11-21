import sys,json,argparse,pickle
sys.path.insert(0,'src')
from integrated_02196 import Unified296
p=argparse.ArgumentParser();p.add_argument('--seed',type=int,default=9711);p.add_argument('--conservative',action='store_true');p.add_argument('--checkpoint');p.add_argument('--days',type=int,default=180);a=p.parse_args()
s=Unified296(seed=a.seed,reproductive_ecology=True,juvenile_foraging=True,capacity_scale=.5,growth_allocation=True,edible_budget=3,scheduled_funding=True,conservative_access=a.conservative)
for _ in range(a.days):
 s.step()
 if s.days==30 and a.checkpoint:s.save(a.checkpoint)
 if s.days in (30,60,120,180):
  b=s.bridge;au=s.host.book.audit()
  print(json.dumps(dict(seed=a.seed,arm='conservative' if a.conservative else 'control',day=s.days,living=sum(x.alive for x in b.actors.values()),births=b.stats['birth'],g1_adults=sum(x.alive and x.generation==1 and x.stage=='adult' for x in b.actors.values()),g2_births=sum(x.generation>=2 for x in b.actors.values()),tree=b.tree.state,mass_error=au['mass_error'],energy_error=au['energy_error'],rejections=au.get('rejections',0),funded_events=sum(bool(e.get('funded')) for e in s.edible_events))),flush=True)
