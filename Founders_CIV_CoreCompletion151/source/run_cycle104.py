"""Cycle104: complete missing matched arm and verify 30+150 replay."""
import argparse,sys,json,pickle,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES

def summary(s):
 a=s.host.book.audit(); living=[x for x in s.bridge.actors.values() if x.alive]
 return {'day':s.host.sim.tick,'living':len(living),'g1_alive':sum(getattr(x,'generation',0)==1 for x in living),'g1_adults':sum(getattr(x,'generation',0)==1 and getattr(x,'age',0)>=getattr(x,'maturity_age',float('inf')) for x in living),'g2_births':sum(getattr(x,'generation',0)>=2 for x in s.bridge.actors.values()),'tree':str(s.bridge.tree.state),'mass_error':a['mass_error'],'energy_error':a['energy_error'],'rejections':a['rejections']}
def run(out,seed,density,profile,family,days):
 s=Unified260(seed=seed,counts={k:density*2 for k in SPECIES},capacity_scale=.5,capacity_profile=profile,family_benefits=family,resource_aware_family=family)
 rows=[]
 for day in range(1,days+1):
  s.step()
  if day==30:
   with (out/'day30_checkpoint.pkl').open('wb') as f:pickle.dump(s,f)
  if day in (30,60,120,180):
   r={'seed':seed,'density':density,'profile':profile,'family':family,**summary(s)}
   assert abs(r['mass_error'])<1e-5 and abs(r['energy_error'])<1e-5 and r['rejections']==0,r
   rows.append(r)
 (out/'results.json').write_text(json.dumps(rows,indent=2))
 if days==180:
  with (out/'day30_checkpoint.pkl').open('rb') as f:t=pickle.load(f)
  for _ in range(150):t.step()
  # Exact state comparison via deterministic pickle representation and explicit Book/map/cognition snapshots
  replay={'summary_equal':summary(s)==summary(t),'mass_equal':dict(s.host.book.mass)==dict(t.host.book.mass),'energy_equal':dict(s.host.book.energy)==dict(t.host.book.energy),'actor_equal':pickle.dumps(s.bridge.actors)==pickle.dumps(t.bridge.actors),'tree_state_equal':s.bridge.tree.state==t.bridge.tree.state,'events_equal':s.bridge.events==t.bridge.events}
  (out/'replay.json').write_text(json.dumps(replay,indent=2))
  assert all(replay.values()),replay
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--seed',type=int,default=9712);p.add_argument('--density',type=int,default=8);p.add_argument('--profile',default='browse_heavy');p.add_argument('--family',action='store_true');p.add_argument('--days',type=int,default=60);a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True);run(out,a.seed,a.density,a.profile,a.family,a.days)
