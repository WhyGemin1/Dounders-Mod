import sys,json,argparse
sys.path.insert(0,'src')
from integrated_02192 import Unified292
p=argparse.ArgumentParser();p.add_argument('--days',type=int,default=30);p.add_argument('--seed',type=int,default=9711);p.add_argument('--budget',type=int,default=0);p.add_argument('--checkpoint');p.add_argument('--density',type=float,default=.5);a=p.parse_args()
s=Unified292(seed=a.seed,reproductive_ecology=True,juvenile_foraging=True,capacity_scale=a.density,growth_allocation=True,edible_budget=a.budget)
for _ in range(a.days):s.step()
if a.checkpoint:s.save(a.checkpoint)
b=s.bridge;au=s.host.book.audit()
print(json.dumps(dict(seed=a.seed,budget=a.budget,density=a.density,days=s.days,living=sum(x.alive for x in b.actors.values()),births=b.stats['birth'],g1_adults=sum(x.alive and x.generation==1 and x.stage=='adult' for x in b.actors.values()),g2_births=sum(x.generation>=2 for x in b.actors.values()),tree=b.tree.state,mass_error=au['mass_error'],energy_error=au['energy_error'],rejections=au.get('rejections',0),edible_events=s.edible_events)))
