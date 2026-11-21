"""Cycle007 opt-in ledger-conserving digestion probe; canonical unmodified."""
from __future__ import annotations
import pickle
from unified_02115 import Unified215
from digestion_02120 import HabitatBridge220

class Unified220(Unified215):
    def __init__(self,seed=9711,governance='collective',counts=None,digestion=False):
        # Parent builds one host, one World Tree, one Book and baseline bridge.
        # Avoid constructing a duplicate physical world when enabling digestion.
        self.digestion=bool(digestion)
        if not self.digestion:
            super().__init__(seed=seed,governance=governance,counts=counts)
        else:
            from living_tree_runner import LivingTreeRunner
            self.host=LivingTreeRunner(seed=seed,governance=governance)
            self.bridge=HabitatBridge220(self.host.sim.world_trees.worlds[self.host.tree_id],seed,counts)
            self.seed=seed;self.days=0;self.history=[]
            self._check()
    def report(self):
        result=super().report()
        result['digestive_energy_mode']='experimental_funded' if self.digestion else 'v0.21.19_control'
        if self.digestion:result['embodied_energy']=self.bridge.census()
        return result
    @classmethod
    def load(cls,path):
        with open(path,'rb') as f:obj=pickle.load(f)
        if type(obj) is not cls:raise ValueError('checkpoint revision mismatch')
        obj._check()
        return obj
