import sys,json,argparse
sys.path.insert(0,'src')
from integrated_02189 import Unified289
p=argparse.ArgumentParser();p.add_argument('--days',type=int,default=30);p.add_argument('--seed',type=int,default=9711);p.add_argument('--renewal',type=float,default=0);p.add_argument('--checkpoint');a=p.parse_args()
s=Unified289(seed=a.seed,reproductive_ecology=True,juvenile_foraging=True,capacity_scale=.5,growth_allocation=True,renewal_scale=a.renewal)
for _ in range(a.days):s.step()
b=s.bridge;au=s.host.book.audit()
if a.checkpoint:s.save(a.checkpoint)
print(json.dumps(dict(seed=a.seed,renewal=a.renewal,days=s.days,living=sum(x.alive for x in b.actors.values()),births=b.stats['birth'],g1_adults=sum(x.alive and x.generation==1 and x.stage=='adult' for x in b.actors.values()),g2_births=sum(x.generation>=2 for x in b.actors.values()),tree=b.tree.state,mass_error=au['mass_error'],energy_error=au['energy_error'],rejections=au.get('rejections',0),renewals=s.renewals)))
