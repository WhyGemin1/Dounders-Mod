"""Reproducible matched-seed Cycle142 validation. Never implies canonical promotion.

Example: PYTHONPATH=src:world023024 python run_five_phase_142.py --seeds 100001 100002 --days 180
"""
import argparse,csv,json
from collections import Counter
from core_physiology_v2 import UnifiedCoreV2
from five_phase_core_142 import UnifiedFivePhase142

p=argparse.ArgumentParser()
p.add_argument('--seeds',type=int,nargs='+',default=[100001,100002,100003])
p.add_argument('--days',type=int,default=180)
p.add_argument('--controls',action='store_true')
p.add_argument('--disable-funding',action='store_true')
p.add_argument('--drought-start',type=int)
p.add_argument('--drought-end',type=int)
p.add_argument('--output',default='cycle142_matched_results.csv')
a=p.parse_args()
rows=[]
for seed in a.seeds:
 for arm in (['core_v2','five_phase_142'] if a.controls else ['five_phase_142']):
  sim=(UnifiedCoreV2(seed=seed,founder_world_support=not a.disable_funding)
       if arm=='core_v2' else UnifiedFivePhase142(seed=seed,founder_world_support=not a.disable_funding))
  for day in range(1,a.days+1):
   if a.drought_start is not None:
    sim.bridge.tree.precipitation_factor=(.25 if a.drought_start<=day <= (a.drought_end or a.days) else 1.)
   sim.step()
   if day not in (30,180,360,720,1080) and day!=a.days:continue
   br=sim.bridge;dead=Counter(e.get('cause') for e in br.events if e['event']=='death')
   pop=Counter(x.species for x in br.actors.values() if x.alive)
   row={'seed':seed,'arm':arm,'day':day,'drought':a.drought_start is not None,
     'founder_support':not a.disable_funding,'tree_state':br.tree.state,
     'native_alive':br.tree.population,'bridge_alive':sum(pop.values()),
     'species_alive':len(pop),'hounds':pop['ridge_hound'],'foxes':pop['red_fox'],
     'jackals':pop['golden_jackal'],'rabbits':pop['burrow_rabbit'],
     'elephants':pop['forest_elephant'],'mammoths':pop['woolly_mammoth'],
     'births':sum(e['event']=='birth' for e in br.events),
     'death_physiological_failure':dead['physiological_failure'],
     'death_predation':dead['predation'],'death_world_collapse':dead['world_tree_collapse'],
     'book_rejections':sim.host.book.audit()['rejections'],
     'mass_error':sim.host.book.audit()['mass_error'],
     'energy_error':sim.host.book.audit()['energy_error'],
     'ingested_energy':br.physiology_metrics.get('ingested_energy',0),
     'absorbed_energy':br.physiology_metrics.get('absorbed_energy',0),
     'paired_meals':br.physiology_metrics.get('paired_lot_meals',0),
     'kills':br.physiology_metrics.get('kills',0),
     'native_paired_meals':br.tree.counters.get('native_paired_meals',0)}
   rows.append(row)
   print(json.dumps({k:row[k] for k in ('seed','arm','day','tree_state','bridge_alive',
                'hounds','foxes','jackals','elephants','mammoths','births','book_rejections')},sort_keys=True),flush=True)
with open(a.output,'w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('Saved',a.output,len(rows),'records')
