"""Opt-in finite dose factorial; deliberately separate from canonical schedulers."""
import hashlib,json,os,pickle,math
from pathlib import Path
from factorial_021126 import configuration
from src.integrated_02160 import Unified260
from src.habitat_bridge import SPECIES
from src.interworld_split_021121 import fund_split_shipment
from src.generation_audit_021108 import generation_metrics

def dose_config(seed,density=8,capacity=.5,family=True,memory=True,dose=0.):
    if not isinstance(dose,(float,int)) or not math.isfinite(dose) or dose<0 or dose>2:raise ValueError('invalid finite dose')
    cfg=configuration(seed,density,capacity,family,memory,funded=dose>0)
    cfg['dose']=float(dose)
    return cfg

def start(cfg):
    sim=Unified260(seed=cfg['seed'],counts={k:cfg['density'] for k in SPECIES},capacity_scale=cfg['capacity'],family_benefits=cfg['family'],resource_aware_family=cfg['memory'])
    if cfg['dose']:
        d=cfg['dose']
        fund_split_shipment(sim.bridge.tree,.5,biomass=2*d,chemical=d,transport=.1*d)
    return sim

def observe(sim,day,cfg):
    audit=sim.host.book.audit()
    if audit['rejections'] or abs(audit['mass_error'])>1e-5 or abs(audit['energy_error'])>1e-5:raise AssertionError('Book conservation failed')
    return dict(configuration=cfg,day=day,tick=sim.host.sim.tick,living=sum(a.alive for a in sim.bridge.actors.values()),tree_state=str(sim.bridge.tree.state),book=audit,generations=generation_metrics(sim.bridge))

def run(cfg,milestones,folder):
    if not milestones or any(type(x)!=int or x<1 for x in milestones) or any(b<=a for a,b in zip(milestones,milestones[1:])):raise ValueError('invalid milestones')
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    key=hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest()[:16]
    if any(folder.glob(key+'*')):raise FileExistsError('arm already exists; no overwrite')
    sim=start(cfg);rows=[];last=0
    for day in milestones:
        for _ in range(day-last):sim.step()
        row=observe(sim,day,cfg);rows.append(row)
        blob=pickle.dumps(sim,protocol=pickle.HIGHEST_PROTOCOL)
        snap=folder/(key+f'.day{day}.pkl');temp=snap.with_suffix('.tmp')
        with open(temp,'wb') as f:f.write(blob);f.flush();os.fsync(f.fileno())
        os.replace(temp,snap)
        row['checkpoint_sha256']=hashlib.sha256(blob).hexdigest()
        last=day
    journal=folder/(key+'.jsonl');temp=journal.with_suffix('.tmp')
    with open(temp,'w') as f:
        for r in rows:f.write(json.dumps(r,sort_keys=True,default=str)+'\n')
        f.flush();os.fsync(f.fileno())
    os.replace(temp,journal)
    return rows

def replay(cfg,folder,day,target):
    folder=Path(folder);key=hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest()[:16]
    rows=[json.loads(s) for s in (folder/(key+'.jsonl')).read_text().splitlines()]
    row=next(r for r in rows if r['day']==day)
    raw=(folder/(key+f'.day{day}.pkl')).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=row['checkpoint_sha256']:raise ValueError('snapshot hash mismatch')
    sim=pickle.loads(raw)
    if sim.host.sim.tick!=row['tick']:raise ValueError('snapshot clock mismatch')
    for _ in range(target-day):sim.step()
    return observe(sim,target,cfg)
