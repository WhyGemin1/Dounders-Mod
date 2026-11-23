"""Reject provenance-incompatible saved checkpoints before deterministic replay claims."""
import hashlib, json, pickle
from pathlib import Path
from diagnose_replay_021124 import build

def file_sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def signature(s):
    book=s.host.book
    return {'tick':s.host.sim.tick,'book_mass':dict(book.mass),'book_energy':dict(book.energy),
            'events':list(s.bridge.events),'actors':{str(k):repr(v.__dict__) for k,v in s.bridge.actors.items()},
            'tree_state':str(s.bridge.tree.state)}

def audit_checkpoint(path,seed=9711,fraction=.5,checkpoint_day=30,advance=1):
    path=Path(path)
    with path.open('rb') as f: restored=pickle.load(f)
    fresh=build(seed,fraction)
    for _ in range(checkpoint_day):fresh.step()
    a,b=signature(fresh),signature(restored)
    at_checkpoint={k:a[k]==b[k] for k in a}
    for _ in range(advance):fresh.step();restored.step()
    c,d=signature(fresh),signature(restored)
    after={k:c[k]==d[k] for k in c}
    return {'checkpoint_sha256':file_sha256(path),'seed':seed,'fraction':fraction,'checkpoint_day':checkpoint_day,
            'advance':advance,'at_checkpoint':at_checkpoint,'after_advance':after,
            'exact_checkpoint':all(at_checkpoint.values()),'exact_replay':all(after.values()),
            'first_divergence':next((k for k in a if not at_checkpoint[k]),None)}
