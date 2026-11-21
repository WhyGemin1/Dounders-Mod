"""Fail-closed, reversible C006 scheduler integration for Core151/WORLD024.

Run against the extracted C004 canonical source; --rollback restores exactly the
reviewed baseline. Refuses unknown source, missing anchors, and double apply.
"""
import argparse
import hashlib
from pathlib import Path

BASE_SHA = '6490d0bf20f4b634d67ce4125213d5693e0b60e259edf2a74a693f314e18b1be'
TARGET_SHA = '536d903e344dd2529a9244b4c16daab3f4d4442256de9b991311bb025c30a58f'
CHANGES = (
    ("        if self._energy(a)<.19:return props",
     """        if self._energy(a)<.19:
            # Low stored energy cannot veto eating or observation-based collection.
            from founders_civ.core.founder_harvesting import propose_harvest,propose_ingestion
            props.extend(propose_harvest(self,a))
            props.extend(propose_ingestion(self,a))
            return props"""),
    ("""        if self.founder_harvest_enabled:
            props.extend(propose_harvest(self,a))
        return props""",
     """        if self.founder_harvest_enabled:
            props.extend(propose_harvest(self,a))
            from founders_civ.core.founder_harvesting import propose_ingestion
            props.extend(propose_ingestion(self,a))
        return props"""),
    ("""            if action=='tree_research':return self.world_trees.worlds[meta].study(a)""",
     """            if action=='tree_ingest':
                from founders_civ.core.founder_harvesting import perform_ingestion
                return perform_ingestion(self,a,meta)
            if action=='tree_research':return self.world_trees.worlds[meta].study(a)"""),
)

def apply(path, rollback=False):
    path=Path(path)
    original=path.read_bytes()
    digest=hashlib.sha256(original).hexdigest()
    expected=TARGET_SHA if rollback else BASE_SHA
    if digest != expected:
        raise ValueError(f'FAIL CLOSED: expected {expected}, found {digest}')
    text=original.decode('utf-8')
    for old,new in CHANGES:
        source,dest=(new,old) if rollback else (old,new)
        if text.count(source)!=1:raise ValueError('FAIL CLOSED: patch anchor not unique')
        text=text.replace(source,dest,1)
    result=text.encode('utf-8')
    desired=BASE_SHA if rollback else TARGET_SHA
    if hashlib.sha256(result).hexdigest()!=desired:
        raise ValueError('FAIL CLOSED: output SHA mismatch')
    path.write_bytes(result)
    return desired

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('world_integration_py',type=Path)
    p.add_argument('--rollback',action='store_true')
    a=p.parse_args()
    print(apply(a.world_integration_py,a.rollback))
