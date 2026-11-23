import sys,json,argparse
sys.path.insert(0,'src')
from integrated_02190 import Unified290
p=argparse.ArgumentParser();p.add_argument('--days',type=int,default=30);p.add_argument('--seed',type=int,default=9711);p.add_argument('--budget',type=int,default=0);p.add_argument('--checkpoint');a=p.parse_args()
s=Unified290(seed=a.seed,reproductive_ecology=True,juvenile_foraging=True,capacity_scale=.5,growth_allocation=True,policy_budget=a.budget)
for _ in range(a.days):s.step()
if a.checkpoint:s.save(a.checkpoint)
b=s.bridge;au=s.host.book.audit()
print(json.dumps(dict(seed=a.seed,budget=a.budget,days=s.days,living=sum(x.alive for x in b.actors.values()),births=b.stats['birth'],g1_adults=sum(x.alive and x.generation==1 and x.stage=='adult' for x in b.actors.values()),g2_births=sum(x.generation>=2 for x in b.actors.values()),tree=b.tree.state,mass_error=au['mass_error'],energy_error=au['energy_error'],rejections=au.get('rejections',0),policy_events=s.policy_events)))
