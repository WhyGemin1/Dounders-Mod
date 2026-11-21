"""Paired pilot; ecological effects are provisional (not calibrated)."""
import sys,csv,json,argparse
sys.path.insert(0,'src')
from core_physiology_v2 import UnifiedCoreV2
p=argparse.ArgumentParser();p.add_argument('--days',type=int,default=60);p.add_argument('--seeds',type=int,nargs='+',default=[100001,100002]);a=p.parse_args()
rows=[]
for seed in a.seeds:
 for flag in (False,True):
  sim=UnifiedCoreV2(seed=seed,founder_world_support=flag)
  for day in range(a.days):sim.step()
  b=sim.host.book;tree=sim.bridge.tree
  state=sim.bridge.physiology_report()
  rows.append(dict(seed=seed,funding=flag,day=sim.days,alive=state['animals_alive'],
    hounds=sum(x.alive and x.species=='ridge_hound' for x in sim.bridge.actors.values()),
    elephants=sum(x.alive and x.species in ('forest_elephant','woolly_mammoth') for x in sim.bridge.actors.values()),
    founder_energy=sum(b.energy['founder:'+fid] for fid in sim.host.sim.founders.people),
    tree_sun=sum(b.energy[tree.acct('sun',h)] for h in tree.habitats),
    tree_chem=sum(b.energy[tree.acct('chem',h)] for h in tree.habitats),
    tree_plants=sum(b.mass[tree.acct('plant',h)] for h in tree.habitats),
    support_energy=(sum(v for k,v in sim.world_support.totals.items() if k.endswith('_energy')) if flag else 0),
    absorbed_energy=state['metrics'].get('absorbed_energy',0),
    ledger_rejections=b.audit()['rejections']))
 print(f'seed {seed} completed',flush=True)
with open('world_funding_141_results.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
print(json.dumps(rows,indent=2))
