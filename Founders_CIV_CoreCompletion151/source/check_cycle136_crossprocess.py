import argparse,hashlib,json,pickle
from pathlib import Path
from experiment_cycle136 import fingerprint,summarize136,cohort_audit
x=argparse.ArgumentParser();x.add_argument('--seed',type=int,required=True);x.add_argument('--assist',type=int,required=True);x.add_argument('--output',required=True)
a=x.parse_args();p=Path(a.output);base=f'C136_seed{a.seed}_assist{a.assist}'
meta=json.loads((p/(base+'.progress.json')).read_text());orig=pickle.loads((p/(base+'.progress.pkl')).read_bytes());replay=pickle.loads((p/(base+'.day30.pkl')).read_bytes())
for _ in range(meta['last_day']-30):replay.step()
direct=fingerprint(orig);rest=fingerprint(replay)
print(json.dumps({'seed':a.seed,'assist':a.assist,'day':meta['last_day'],'exact':direct==rest,
'direct_sha':direct,'replay_sha':rest,'direct_living':sum(x.alive for x in orig.bridge.actors.values()),'replay_living':sum(x.alive for x in replay.bridge.actors.values()),'direct_book':orig.host.book.audit(),'replay_book':replay.host.book.audit()}),flush=True)
if direct!=rest:raise AssertionError('full state replay mismatch')
