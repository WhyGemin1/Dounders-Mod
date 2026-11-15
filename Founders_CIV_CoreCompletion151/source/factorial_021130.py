"""Cycle130: provenance-checked immutable snapshot replay; no day/tick conflation."""
import hashlib,json,pickle
from pathlib import Path
from factorial_021127 import sha256
from factorial_021129 import run_with_snapshots as _run_snapshots

def run_with_snapshots(cfg,milestones,folder):
    rows=_run_snapshots(cfg,milestones,folder)
    folder=Path(folder);key=snapshot_key(cfg)
    for day in milestones:
        snap=folder/(key+f'.day{day}.pkl')
        with snap.open('rb') as f: sim=pickle.load(f)
        side=folder/(key+f'.day{day}.clock.json')
        side.write_text(json.dumps(dict(day=day,tick=sim.host.sim.tick,sha256=sha256(snap)),sort_keys=True))
    return rows

def snapshot_key(cfg):
    return hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest()[:16]

def verified_snapshot(cfg,day,folder):
    if type(day) is not int or day<1: raise ValueError('invalid day')
    folder=Path(folder); key=snapshot_key(cfg)
    snapshot=folder/(key+f'.day{day}.pkl')
    journal=folder/(key+'.jsonl')
    if not snapshot.exists() or not journal.exists():raise FileNotFoundError('snapshot or journal missing')
    rows=[json.loads(s) for s in journal.read_text().splitlines() if s.strip()]
    matches=[r for r in rows if r['day']==day]
    if len(matches)!=1:raise ValueError('missing or duplicate journal milestone')
    row=matches[0]
    if row['configuration']!=cfg or sha256(snapshot)!=row['checkpoint_sha256']:raise ValueError('snapshot provenance mismatch')
    with snapshot.open('rb') as f:sim=pickle.load(f)
    side=folder/(key+f'.day{day}.clock.json')
    if not side.exists():raise ValueError('missing snapshot clock provenance')
    clock=json.loads(side.read_text())
    if clock!=dict(day=day,tick=sim.host.sim.tick,sha256=sha256(snapshot)):raise ValueError('snapshot clock mismatch')
    return sim,row

def replay_verified(cfg,day,target,folder):
    if type(target) is not int or target<day:raise ValueError('invalid replay target')
    sim,row=verified_snapshot(cfg,day,folder)
    for _ in range(target-day):sim.step()
    audit=sim.host.book.audit()
    if audit['rejections'] or abs(audit['mass_error'])>1e-5 or abs(audit['energy_error'])>1e-5:raise AssertionError('Book conservation failed')
    return dict(day=target,tick=sim.host.sim.tick,book=audit,living=sum(a.alive for a in sim.bridge.actors.values()),tree_state=str(sim.bridge.tree.state))
