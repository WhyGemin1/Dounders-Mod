"""Cycle143 controlled 180-day comparison and exact day30+150 replay."""
import pickle, json, csv, sys, time
from pathlib import Path
from collections import Counter
from five_phase_core_142 import UnifiedFivePhase142
from core_completion_143 import UnifiedCoreCompletion143
OUT=Path(sys.argv[1]);OUT.mkdir(exist_ok=True,parents=True)
rows=[];replays=[]

def fingerprint(s):
 b=s.host.book;t=s.bridge.tree;bridge=s.bridge
 return {
 'book_mass':dict(sorted(b.mass.items())), 'book_energy':dict(sorted(b.energy.items())),
 'book_seq':b.seq, 'book_rejected':b.rejected,'world':t.state,'world_age':t.age,
 'native':[(x.id,x.alive,x.age,x.health,x.habitat,x.generation) for x in sorted(t.residents.values(),key=lambda x:x.id)],
 'bridge':[(x.id,x.alive,x.age,x.condition,x.habitat,x.generation,x.stage) for x in sorted(bridge.actors.values(),key=lambda x:x.id)],
 'bridge_states':str(sorted((k,vars(v)) for k,v in bridge.functional.items())),
 'native_counters':dict(sorted(t.counters.items())),
 'bridge_metrics':dict(sorted(bridge.physiology_metrics.items())),
 'positions':dict(sorted(bridge.positions.items())),
 }
for seed in (100001,100002):
 for arm,klass in [('baseline142',UnifiedFivePhase142),('core143',UnifiedCoreCompletion143)]:
  start=time.monotonic();s=klass(seed=seed)
  ckpt=None
  for d in range(1,181):
   s.step()
   if d==30 and arm=='core143' and seed==100001:
    ckpt=pickle.dumps(s,protocol=pickle.HIGHEST_PROTOCOL)
    (OUT/'Cycle143_seed100001_core_day30_checkpoint.pkl').write_bytes(ckpt)
   if d in (30,60,120,180):
    b=s.host.book;tree=s.bridge.tree
    alive=[x for x in s.bridge.actors.values() if x.alive]
    g1=[x for x in s.bridge.actors.values() if x.generation==1]
    g2=[x for x in s.bridge.actors.values() if x.generation>=2]
    row=dict(seed=seed,arm=arm,day=d,bridge_living=len(alive),native_living=tree.population,
     tree_state=tree.state,g1_births=len(g1),g1_alive=sum(x.alive for x in g1),
     g1_reached_maturity=sum(x.age>=__import__('species_life_02115').PROFILES[x.species].maturity for x in g1),
     g2_births=len(g2),native_births=tree.counters['tree_birth'],
     native_gut_meals=tree.counters['native_gut_meals'] if arm=='core143' else 0,
     native_absorption_events=tree.counters['native_absorption_events'] if arm=='core143' else 0,
     bridge_fee_free_ingestion=s.bridge.physiology_metrics['fee_free_ingestion'] if arm=='core143' else 0,
     book_rejections=b.rejected,book_energy_error=b.audit()['energy_error'])
    rows.append(row)
  if ckpt is not None:
   saved=pickle.loads(ckpt)
   for _ in range(150):saved.step()
   match=fingerprint(s)==fingerprint(saved)
   replays.append(dict(seed=seed,arm=arm,checkpoint_day=30,replayed_days=150,match=match,
                       end_day=180,book_rejections=s.host.book.rejected))
   if not match:raise AssertionError('30+150 replay mismatch')
  print('done',seed,arm,'s',round(time.monotonic()-start,2),rows[-1],flush=True)
with (OUT/'Cycle143_Long_Results.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(OUT/'Cycle143_Long_Results.json').write_text(json.dumps(rows,indent=2))
(OUT/'Cycle143_150day_replay.json').write_text(json.dumps(replays,indent=2))
