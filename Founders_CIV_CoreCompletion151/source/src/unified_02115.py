"""v0.21.15 experimental v0.21.7 life history + true four-habitat Book.

One WORLD-023/024 simulation clock; original World Tree residents remain on
legacy scheduler pending actor-registry unification. No canonical promotion.
"""
import argparse,json,pickle
from pathlib import Path
from unified_02114 import Unified214
from living_tree_runner import LivingTreeRunner
from species_life_02115 import HabitatBridge215

class Unified215(Unified214):
    def __init__(self,seed=9711,governance='collective',counts=None):
        self.host=LivingTreeRunner(seed=seed,governance=governance)
        self.bridge=HabitatBridge215(self.host.sim.world_trees.worlds[self.host.tree_id],seed,counts)
        self.seed=seed;self.days=0;self.history=[]
        self._check()
    def report(self):
        report=super().report()
        report['scope']='experimental life-history/needs bridge v0.21.15 (no second clock or ledger)'
        report['life_history']={k:self.bridge.stats[k] for k in ('conception','birth','failed_birth','parental_care','hunt_attempt','escape','predation','death')}
        return report
    @classmethod
    def load(cls,path):
        with open(path,'rb') as f:obj=pickle.load(f)
        if type(obj) is not cls:raise ValueError('checkpoint type/revision mismatch')
        obj._check()
        return obj

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--seed',type=int,default=9711);p.add_argument('--days',type=int,default=30)
    p.add_argument('--resume');p.add_argument('--checkpoint');p.add_argument('--output',default='results/day30_v02115.json')
    a=p.parse_args()
    sim=Unified215.load(a.resume) if a.resume else Unified215(seed=a.seed)
    report=sim.run(a.days)
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2))
    if a.checkpoint:sim.save(a.checkpoint)
    print(json.dumps({k:v for k,v in report.items() if k!='history'}))
