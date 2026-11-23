"""Cycle123 crash-safe, checkpoint-resumable experimental arm runner.
Never treats a partial milestone journal as a completed arm.
"""
import json, os, pickle, sys, argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from interworld_split_021121 import fund_split_shipment
from generation_audit_021108 import generation_metrics
MILESTONES=(30,60,120,180)
def atomic_bytes(path, data):
    path=Path(path); tmp=path.with_suffix(path.suffix+'.tmp')
    with open(tmp,'wb') as f:
        f.write(data); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,path)
def run(seed,fraction,output,days=180):
    if days not in MILESTONES: raise ValueError('days must be a milestone')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    name=f'seed{seed}_fraction{fraction:g}'
    journal=output/(name+'.jsonl')
    rows=[json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
    if rows:
        assert all(r['seed']==seed and r['floodplain_fraction']==fraction for r in rows)
        assert [r['day'] for r in rows]==list(MILESTONES[:len(rows)])
        if rows[-1]['day']>=days:return rows
    last=rows[-1]['day'] if rows else 0
    checkpoint=output/(name+f'_day{last}.pkl')
    if last and checkpoint.exists():
        with checkpoint.open('rb') as f:s=pickle.load(f)
        if s.host.sim.tick!=rows[-1]['tick']:raise ValueError('checkpoint/journal clock mismatch')
    else:
        # Recompute rather than silently skipping already-journaled days.
        s=Unified260(seed=seed,counts={k:8 for k in SPECIES},capacity_scale=.5,family_benefits=True,resource_aware_family=True)
        fund_split_shipment(s.bridge.tree,fraction)
        for _ in range(last):s.step()
        if last and s.host.sim.tick!=rows[-1]['tick']:raise ValueError('recomputed clock mismatch')
    for day in range(last+1,days+1):
        s.step()
        if day in MILESTONES:
            audit=s.host.book.audit()
            assert audit['rejections']==0 and abs(audit['mass_error'])<1e-5 and abs(audit['energy_error'])<1e-5
            row=dict(seed=seed,floodplain_fraction=fraction,day=day,tick=s.host.sim.tick,living=sum(a.alive for a in s.bridge.actors.values()),tree_state=s.bridge.tree.state,book_rejections=audit['rejections'],mass_error=audit['mass_error'],energy_error=audit['energy_error'],**generation_metrics(s.bridge))
            # Checkpoint first: a crash after checkpoint but before journal is safe (recompute).
            import io
            b=io.BytesIO();pickle.dump(s,b)
            atomic_bytes(output/(name+f'_day{day}.pkl'),b.getvalue())
            rows.append(row)
            atomic_bytes(journal,(''.join(json.dumps(r,default=str)+'\n' for r in rows)).encode())
    return rows
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,default=9711);p.add_argument('--fraction',type=float,default=.5);p.add_argument('--days',type=int,default=180);p.add_argument('--output',default='/mnt/data/cycle123')
    a=p.parse_args();print(json.dumps(run(a.seed,a.fraction,a.output,a.days),default=str))
