"""v0.21.14 experimental upgrade: one WORLD-023/024 clock with migration
and explicit carcass/decay accounts, retaining v0.21.13 as a comparison arm."""
import argparse,json,pickle
from pathlib import Path
from unified_02113 import Unified213
from habitat_bridge_02114 import HabitatBridge214

class Unified214(Unified213):
    def __init__(self,seed=9711,governance='collective',counts=None):
        from living_tree_runner import LivingTreeRunner
        self.host=LivingTreeRunner(seed=seed,governance=governance)
        self.bridge=HabitatBridge214(self.host.sim.world_trees.worlds[self.host.tree_id],seed,counts)
        self.seed=seed;self.days=0;self.history=[]
        self._check()

    def _check(self):
        super()._check()
        self.bridge._check_registry()

    def report(self):
        out=super().report()
        out['registry_census']=self.bridge.census()
        out['scope']='experimental v0.21.14 adjacent migrations and carrion; v0.21.7 scheduler NOT integrated'
        return out

    @classmethod
    def load(cls,path):
        with open(path,'rb') as f: obj=pickle.load(f)
        if not isinstance(obj,cls):raise ValueError('unexpected checkpoint type')
        obj._check()
        return obj

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--seed',type=int,default=9711);p.add_argument('--days',type=int,default=30)
    p.add_argument('--resume');p.add_argument('--checkpoint');p.add_argument('--output',default='results/day30_v02114.json')
    p.add_argument('--governance',default='collective',choices=['collective','owner','fragmented','none'])
    a=p.parse_args()
    sim=Unified214.load(a.resume) if a.resume else Unified214(seed=a.seed,governance=a.governance)
    result=sim.run(a.days)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2))
    if a.checkpoint:sim.save(a.checkpoint)
    print(json.dumps({k:v for k,v in result.items() if k!='history'}))
