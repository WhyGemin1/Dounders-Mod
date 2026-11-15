import sys,json,argparse
sys.path.insert(0,'src')
from integrated_02194 import Unified294
p=argparse.ArgumentParser();p.add_argument('--days',type=int,default=30);p.add_argument('--seed',type=int,default=9711);p.add_argument('--budget',type=int,default=0);p.add_argument('--density',type=float,default=.5);p.add_argument('--scheduled',action='store_true');p.add_argument('--checkpoint');a=p.parse_args()
s=Unified294(seed=a.seed,reproductive_ecology=True,juvenile_foraging=True,capacity_scale=a.density,growth_allocation=True,edible_budget=a.budget,scheduled_funding=a.scheduled)
for _ in range(a.days):s.step()
if a.checkpoint:s.save(a.checkpoint)
audit=s.host.book.audit(); print(json.dumps({'seed':a.seed,'days':s.days,'density':a.density,'budget':a.budget,'scheduled':a.scheduled,'snapshots':s.access_snapshots,'events':s.edible_events,'audit':audit,'tree':s.bridge.tree.state,'births':s.bridge.stats['birth']},default=str))
