"""Fail-closed checkpoint integrity and durable milestone journal for factorial arms."""
import hashlib,json,os
from pathlib import Path
from factorial_021126 import run_arm

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def run_milestones(cfg, milestones, folder):
    folder=Path(folder); folder.mkdir(parents=True,exist_ok=True)
    key=hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest()[:16]
    checkpoint=folder/(key+'.pkl'); metadata=folder/(key+'.json')
    journal=folder/(key+'.jsonl')
    if checkpoint.exists():
        if not metadata.exists():raise ValueError('missing checkpoint metadata')
        m=json.loads(metadata.read_text())
        if m.get('checkpoint_sha256') and m['checkpoint_sha256']!=sha256(checkpoint):raise ValueError('checkpoint hash mismatch')
    out=[]
    for day in milestones:
        if not isinstance(day,int) or day<0:raise ValueError('invalid milestone')
        result=run_arm(cfg,day,folder)
        m=json.loads(metadata.read_text());m['checkpoint_sha256']=sha256(checkpoint)
        tmp=metadata.with_suffix('.json.tmp');tmp.write_text(json.dumps(m,sort_keys=True));os.replace(tmp,metadata)
        record={'day':day,'configuration':cfg,'checkpoint_sha256':m['checkpoint_sha256'],'living':result['living'],'generations':result['generations'],'book':result['book'],'tree_state':str(result['tree_state'])}
        with journal.open('a') as f:f.write(json.dumps(record,default=str,sort_keys=True)+'\n');f.flush();os.fsync(f.fileno())
        out.append(record)
    return out
