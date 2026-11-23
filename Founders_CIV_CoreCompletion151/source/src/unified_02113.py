"""v0.21.13 experimental WORLD-023/024 host with physical five-guild cohort.
This does not yet integrate the full v0.21.7 LifeHistoryEcology scheduler.
"""
import sys,json,pickle,argparse
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from living_tree_runner import LivingTreeRunner
from habitat_bridge import HabitatBridge
class Unified213:
    def __init__(self,seed=9711,governance='collective',counts=None):
        self.host=LivingTreeRunner(seed=seed,governance=governance)
        self.bridge=HabitatBridge(self.host.sim.world_trees.worlds[self.host.tree_id],seed,counts)
        self.seed=seed;self.days=0;self.history=[]
        self._check()
    def _check(self):
        assert self.host.book is self.bridge.book is self.host.sim.book
        assert self.host.sim.tick==self.host.sim.ecology.day
        assert self.bridge.day==self.days
        self.host.book.audit()
    def step(self):
        self.host.step();self.days+=1
        self.bridge.step(self.days)
        self._check()
        if self.days==1 or self.days%30==0:
            self.history.append({'day':self.days,'species':self.bridge.report(),'tree_state':self.bridge.tree.state,'tree_population':self.bridge.tree.population,'tree_plant_mass':sum(self.host.book.mass[self.bridge.tree.acct('plant',p)] for p in self.bridge.tree.habitats),'ledger':self.host.book.audit()})
    def run(self,days):
        for _ in range(days):self.step()
        return self.report()
    def report(self):
        return {'seed':self.seed,'days':self.days,'founders':len(self.host.sim.founders.people),'species':self.bridge.report(),'tree_state':self.bridge.tree.state,'tree_population':self.bridge.tree.population,'bridge_events':dict(self.bridge.stats),'ledger':self.host.book.audit(),'history':self.history,'scope':'experimental five-guild ledger bridge; v0.21.7 full ecology NOT integrated'}
    def save(self,path):
        with open(path,'wb') as f:pickle.dump(self,f,pickle.HIGHEST_PROTOCOL)
    @classmethod
    def load(cls,path):
        with open(path,'rb') as f:obj=pickle.load(f)
        obj._check();return obj
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,default=9711);p.add_argument('--days',type=int,default=30);p.add_argument('--resume');p.add_argument('--checkpoint');p.add_argument('--output',default='results/run.json');p.add_argument('--governance',choices=['collective','owner','fragmented','none'],default='collective');a=p.parse_args()
    sim=Unified213.load(a.resume) if a.resume else Unified213(seed=a.seed,governance=a.governance)
    result=sim.run(a.days)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2))
    if a.checkpoint:sim.save(a.checkpoint)
    print(json.dumps({k:v for k,v in result.items() if k!='history'}))
