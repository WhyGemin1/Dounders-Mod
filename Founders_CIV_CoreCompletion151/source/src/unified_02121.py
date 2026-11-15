"""Cycle008 experimental A-020: select existing digestion vs funded hound scavenging.

No canonical model replacement. Two resident schedulers remain distinct.
"""
from unified_02120 import Unified220
from digestion_02121 import HabitatBridge221

class Unified221(Unified220):
    def __init__(self,seed=9711,governance='collective',counts=None,
                 digestion=False,predator_scavenging=False):
        self.predator_scavenging=bool(predator_scavenging)
        if self.predator_scavenging and not digestion:
            raise ValueError('predator scavenging requires funded digestion')
        if self.predator_scavenging:
            from living_tree_runner import LivingTreeRunner
            self.digestion=True
            self.host=LivingTreeRunner(seed=seed,governance=governance)
            self.bridge=HabitatBridge221(
                self.host.sim.world_trees.worlds[self.host.tree_id],seed,counts)
            self.seed=seed;self.days=0;self.history=[]
            self._check()
        else:
            super().__init__(seed=seed,governance=governance,
                             counts=counts,digestion=digestion)

    def report(self):
        result=super().report()
        result['predator_scavenging']='opt_in' if self.predator_scavenging else 'disabled'
        return result
