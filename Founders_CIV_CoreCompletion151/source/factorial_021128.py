"""Fail-closed milestone ordering and journal/checkpoint agreement for experimental arms."""
import hashlib,json
from pathlib import Path
from factorial_021127 import run_milestones,sha256

def run_verified(cfg,milestones,folder):
    if not milestones or any(type(d) is not int or d<1 for d in milestones) or any(b<=a for a,b in zip(milestones,milestones[1:])):
        raise ValueError('milestones must be strictly increasing positive integers')
    folder=Path(folder)
    key=hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest()[:16]
    meta=folder/(key+'.json'); journal=folder/(key+'.jsonl'); checkpoint=folder/(key+'.pkl')
    if meta.exists() or journal.exists() or checkpoint.exists():
        if not all(p.exists() for p in (meta,journal,checkpoint)):
            raise ValueError('incomplete checkpoint/journal transaction')
        m=json.loads(meta.read_text()); lines=[json.loads(x) for x in journal.read_text().splitlines() if x.strip()]
        if not lines or lines[-1]['day']!=m['day'] or lines[-1]['checkpoint_sha256']!=sha256(checkpoint):
            raise ValueError('checkpoint/journal divergence')
        if milestones[0]<=m['day']:raise ValueError('milestone already completed')
    return run_milestones(cfg,milestones,folder)
