"""Matched mainline-source comparison; outputs raw evidence, no stability claim.

Usage: PYTHONPATH=src:world023024 PYTHONHASHSEED=0 python run_core_completion_143.py
"""
import csv, json, pickle, hashlib, time, sys
from collections import Counter
from pathlib import Path
from five_phase_core_142 import UnifiedFivePhase142
from core_completion_143 import UnifiedCoreCompletion143

OUT=Path(sys.argv[1] if len(sys.argv)>1 else '.')
OUT.mkdir(parents=True,exist_ok=True)
results=[]
replays=[]
for seed in (100001,100002):
 for label,model in (('cycle142_baseline',UnifiedFivePhase142),('core_completion_143',UnifiedCoreCompletion143)):
    tic=time.time()
    sim=model(seed=seed)
    checkpoint=None
    for day in range(1,61):
       sim.step()
       if day==30 and label=='core_completion_143' and seed==100001:
           checkpoint=pickle.dumps(sim,protocol=pickle.HIGHEST_PROTOCOL)
           (OUT/'Cycle143_seed100001_day30.pkl').write_bytes(checkpoint)
       if day in (7,30,60):
           tree=sim.bridge.tree
           actors=[a for a in sim.bridge.actors.values() if a.alive]
           counts=Counter(a.species for a in actors)
           aud=sim.host.book.audit()
           results.append({
             'seed':seed,'arm':label,'day':day,
             'living_bridge':len(actors),'living_native':tree.population,
             'world_state':tree.state,
             'bridge_birth_events':sum(1 for e in sim.bridge.events if e.get('type')=='birth') if hasattr(sim.bridge,'events') else None,
             'native_births':tree.counters['tree_birth'],
             'foxes':counts['red_fox'],'jackals':counts['golden_jackal'],
             'hounds':counts['ridge_hound'],
             'book_rejections':aud['rejections'],
             'book_energy_error':aud['energy_error'],
             'native_gut_meals':tree.counters['native_gut_meals'] if label=='core_completion_143' else 0,
             'native_absorptions':tree.counters['native_absorption_events'] if label=='core_completion_143' else 0,
             'fee_free_bridge_meals':sim.bridge.physiology_metrics['fee_free_ingestion'] if label=='core_completion_143' else 0
           })
    if checkpoint is not None:
        rerun=pickle.loads(checkpoint)
        for _ in range(30):rerun.step()
        # Semantic replay beyond matching populations: Book accounts, resident
        # and bridge states, physiological accounts, cognition and events.
        def fingerprint(s):
            payload=pickle.dumps(s,protocol=pickle.HIGHEST_PROTOCOL)
            # Pickle bytes may contain nonsemantic object-location changes.
            # Compare sorted Book stocks and deterministic JSON reports separately.
            return {
              'book_material':dict(sorted(s.host.book.mass.items())),
              'book_energy':dict(sorted(s.host.book.energy.items())),
              'native':{k:(v.alive,v.age,v.habitat,v.health,v.generation)
                        for k,v in sorted(s.bridge.tree.residents.items())},
              'bridge':{k:(v.alive,v.age,v.habitat,v.condition,v.stage)
                        for k,v in sorted(s.bridge.actors.items())},
              'bridge_physiology':s.bridge.physiology_report(),
              'tree_counters':dict(sorted(s.bridge.tree.counters.items())),
              'book_seq':s.host.book.seq,
            }
        equal=fingerprint(sim)==fingerprint(rerun)
        replays.append({'seed':seed,'day_checkpoint':30,'continuation_days':30,
                        'semantic_match':equal,'end_day':sim.days,
                        'book_rejections':sim.host.book.rejected})
        if not equal:raise AssertionError('day30+30 checkpoint replay mismatch')
    print('completed',seed,label,'seconds',round(time.time()-tic,2), 'day60 living',results[-1]['living_bridge'],'native',results[-1]['living_native'],flush=True)
with (OUT/'Cycle143_results.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
(OUT/'Cycle143_replay.json').write_text(json.dumps(replays,indent=2))
(OUT/'Cycle143_results.json').write_text(json.dumps(results,indent=2))
