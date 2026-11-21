"""Opt-in factorial arm with configuration-bound checkpoint and finite funding."""
import hashlib,json,os,pickle
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from interworld_split_021121 import fund_split_shipment
from generation_audit_021108 import generation_metrics

def configuration(seed, density=8, capacity=.5, family=True, memory=True, funded=True):
    if not isinstance(density,int) or density<1 or density>30: raise ValueError('density out of bounds')
    if not 0.1<=capacity<=2: raise ValueError('capacity out of bounds')
    if memory and not family: raise ValueError('memory requires family')
    if family and density<8: raise ValueError('family pairing requires density >=8')
    return dict(seed=int(seed),density=density,capacity=float(capacity),family=bool(family),memory=bool(memory),funded=bool(funded))

def run_arm(cfg, days, folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    key=hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest()[:16]
    path=folder/(key+'.pkl'); meta=folder/(key+'.json')
    if path.exists():
        if not meta.exists() or json.loads(meta.read_text())['configuration']!=cfg: raise ValueError('checkpoint provenance mismatch')
        with path.open('rb') as f: sim=pickle.load(f)
        start=json.loads(meta.read_text())['day']
        if sim.host.sim.tick!=json.loads(meta.read_text())['tick']: raise ValueError('clock mismatch')
    else:
        sim=Unified260(seed=cfg['seed'],counts={k:cfg['density'] for k in SPECIES},capacity_scale=cfg['capacity'],family_benefits=cfg['family'],resource_aware_family=cfg['memory'])
        if cfg['funded']: fund_split_shipment(sim.bridge.tree,.5)
        start=0
    if days<start:raise ValueError('cannot rewind checkpoint')
    for day in range(start+1,days+1):sim.step()
    audit=sim.host.book.audit()
    if audit['rejections'] or abs(audit['mass_error'])>1e-5 or abs(audit['energy_error'])>1e-5:raise AssertionError('Book conservation failed')
    result=dict(configuration=cfg,day=days,tick=sim.host.sim.tick,living=sum(a.alive for a in sim.bridge.actors.values()),tree_state=sim.bridge.tree.state,book=audit,generations=generation_metrics(sim.bridge))
    # Atomic checkpoint then metadata; a failed metadata write fails closed next time.
    import tempfile
    for dest,data in ((path,pickle.dumps(sim)),(meta,json.dumps(dict(configuration=cfg,day=days,tick=sim.host.sim.tick),sort_keys=True).encode())):
        tmp=dest.with_suffix(dest.suffix+'.tmp')
        with open(tmp,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(tmp,dest)
    return result
