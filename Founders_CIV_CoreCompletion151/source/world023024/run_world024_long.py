"""Five additional fixed-seed 500-cycle persistence diagnostics.
Not counted among the preregistered 100 scenarios.
"""
from multiprocessing import Pool
from pathlib import Path
import csv,json
from run_world024_stress import run
PLANS=[('commons',829,500),('extractive',829,500),('private_option',829,500),('owner_only',829,500),('upkeep_spike',829,500)]
def task(t):
 try:return run(t[1],t[2],t[0],captures=True)
 except Exception as e:return {'profile':t[0],'seed':t[1],'duration':t[2],'error':repr(e)}
if __name__=='__main__':
 o=Path('results/world024/100_stress'); o.mkdir(parents=True,exist_ok=True)
 with Pool(4) as p:
  for r in p.imap_unordered(task,PLANS):
   file=o/f'500_cycle_{r["profile"]}.json'
   file.write_text(json.dumps(r,indent=2))
   print('LONG',r['profile'],'tree',r.get('shared_tree_state'), 'pop',r.get('shared_tree_population'),'private',r.get('private_worlds_active'), 'error',r.get('error'),flush=True)
