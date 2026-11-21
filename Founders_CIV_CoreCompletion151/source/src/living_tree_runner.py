"""v0.21.12 opt-in REAL WORLD-023/024 lifecycle integration validation.
Not yet a five-species bridge to the v0.21.11 LifeHistoryEcology.
"""
import sys, json, pickle, argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'world023024'))
from run_world_tree_pilot import bootstrap
from founders_civ.experimental.world024 import CommonsWorld

class LivingTreeRunner:
    def __init__(self, seed=9711, governance='collective', extraction='careful', horizon=10000):
        def factory(**kw):
            return CommonsWorld(**kw, governance=governance, extraction=extraction, allow_private=False)
        self.sim, self.realm_id, self.tree_id=bootstrap(seed=seed,simulator_class=factory)
        self.sim.mark_shared(self.tree_id)
        self.book=self.sim.book
        self.seed=seed
        self.history=[]
        self.horizon=horizon
        self.bootstrap_tick=self.sim.tick
        self._validate()
    def _validate(self):
        assert self.book is self.sim.ecology.book
        assert self.book is self.sim.world_trees.worlds[self.tree_id].book
        assert len(self.sim.founders.people)==100
        assert set(self.sim.world_trees.worlds[self.tree_id].habitats)=={'forest','grassland','wetland','ridge'}
        assert self.sim.tick==self.sim.ecology.day
        audit=self.book.audit()
        assert abs(audit['mass_error'])<1e-6 and abs(audit['energy_error'])<1e-6
    def step(self):
        before=self.sim.tick
        self.sim.step()
        assert self.sim.tick==before+1
        self._validate()
        tree=self.sim.world_trees.worlds[self.tree_id]
        if self.sim.tick==1 or self.sim.tick%30==0:
            self.history.append({'day':self.sim.tick,'tree_state':tree.state,'tree_population':tree.population,
               'stewards':len(self.sim.stewards),'harvest_mass':self.sim.harvest_mass,
               'habitat_plant_mass':{p:self.book.mass[tree.acct('plant',p)] for p in tree.habitats},
               'ledger':self.book.audit()})
    def run(self,days):
        if days<0 or self.sim.tick+days>self.horizon:raise ValueError('invalid horizon')
        for _ in range(days):self.step()
        return self.report()
    def report(self):
        tree=self.sim.world_trees.worlds[self.tree_id]
        return {'seed':self.seed,'days':self.sim.tick-self.bootstrap_tick,'absolute_tick':self.sim.tick,'tree_id':self.tree_id,'tree_state':tree.state,
            'tree_population':tree.population,'tree_counters':dict(tree.counters),
            'founders':len(self.sim.founders.people),'stewards':len(self.sim.stewards),
            'ecology_species_engine':'WORLD-023 resident grazers + legacy v0.18 ecology (NOT v0.21.7 five-species)',
            'ledger':self.book.audit(),'history':self.history}
    def save(self,path):
        p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('wb') as f:pickle.dump(self,f,pickle.HIGHEST_PROTOCOL)
    @classmethod
    def load(cls,path):
        with open(path,'rb') as f:obj=pickle.load(f)
        if not isinstance(obj,cls):raise ValueError('checkpoint type')
        obj._validate();return obj

def main():
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,default=9711);p.add_argument('--days',type=int,default=30);p.add_argument('--resume');p.add_argument('--checkpoint');p.add_argument('--output',default='results/living_tree.json');p.add_argument('--governance',default='collective',choices=['collective','owner','fragmented','none']);a=p.parse_args()
    s=LivingTreeRunner.load(a.resume) if a.resume else LivingTreeRunner(seed=a.seed,governance=a.governance)
    result=s.run(a.days)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2,default=str))
    if a.checkpoint:s.save(a.checkpoint)
    print(json.dumps({k:v for k,v in result.items() if k!='history'},default=str))
if __name__=='__main__':main()
