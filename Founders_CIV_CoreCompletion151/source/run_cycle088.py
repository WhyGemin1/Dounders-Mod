import sys,json,argparse
sys.path.insert(0,'src')
from integrated_02188 import Unified288
p=argparse.ArgumentParser();p.add_argument('--days',type=int,default=30);p.add_argument('--seed',type=int,default=9711);p.add_argument('--enabled',action='store_true');args=p.parse_args()
s=Unified288(seed=args.seed,reproductive_ecology=True,juvenile_foraging=True,capacity_scale=.5,growth_allocation=True,dependent_nutrition=args.enabled)
for i in range(args.days):s.step()
b=s.bridge;au=s.host.book.audit()
print(json.dumps(dict(seed=args.seed,enabled=args.enabled,days=s.days,living=sum(a.alive for a in b.actors.values()),births=b.stats['birth'],g1_adults=sum(a.alive and a.generation==1 and a.stage=='adult' for a in b.actors.values()),g2_births=sum(a.generation>=2 for a in b.actors.values()),tree=b.tree.state,mass_error=au['mass_error'],energy_error=au['energy_error'],rejections=au.get('rejections',0))),flush=True)
