"""Cycle129: immutable milestone snapshots and fail-closed replay from retained day-30 state."""
import hashlib, json, os, pickle
from pathlib import Path
from factorial_021128 import run_verified
from factorial_021127 import sha256
from factorial_021126 import run_arm

def run_with_snapshots(cfg, milestones, folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    key=hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest()[:16]
    results=[]
    for day in milestones:
        results.extend(run_verified(cfg,[day],folder))
        checkpoint=folder/(key+'.pkl')
        snapshot=folder/(key+f'.day{day}.pkl')
        if snapshot.exists():raise ValueError('snapshot already exists')
        raw=checkpoint.read_bytes()
        temp=snapshot.with_suffix('.pkl.tmp')
        with temp.open('wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        os.replace(temp,snapshot)
        digest=sha256(snapshot)
        if digest!=results[-1]['checkpoint_sha256']:raise AssertionError('snapshot integrity mismatch')
    return results

def replay_snapshot(cfg, day, target, folder):
    folder=Path(folder)
    key=hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest()[:16]
    snapshot=folder/(key+f'.day{day}.pkl')
    if not snapshot.exists():raise FileNotFoundError(snapshot)
    with snapshot.open('rb') as f:sim=pickle.load(f)
    if sim.host.sim.tick<=0:raise ValueError('snapshot clock invalid')
    for _ in range(day,target):sim.step()
    audit=sim.host.book.audit()
    if audit['rejections'] or abs(audit['mass_error'])>1e-5 or abs(audit['energy_error'])>1e-5:raise AssertionError('Book conservation failed')
    return {'day':target,'tick':sim.host.sim.tick,'book':audit,'living':sum(a.alive for a in sim.bridge.actors.values()),'tree_state':str(sim.bridge.tree.state)}
