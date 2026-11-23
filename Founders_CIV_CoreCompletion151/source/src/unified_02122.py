"""Opt-in A-021 mate cues on the existing World Tree Book and clock."""
from unified_02121 import Unified221
from mate_search_02122 import HabitatBridge222
class Unified222(Unified221):
    def __init__(self,seed=9711,governance='collective',counts=None,
                 digestion=False,predator_scavenging=False,mate_search=False):
        self.mate_search=bool(mate_search)
        if mate_search and not digestion:
            raise ValueError('mate search requires funded digestion')
        if mate_search:
            from living_tree_runner import LivingTreeRunner
            self.predator_scavenging=bool(predator_scavenging)
            self.digestion=True
            self.host=LivingTreeRunner(seed=seed,governance=governance)
            self.bridge=HabitatBridge222(self.host.sim.world_trees.worlds[self.host.tree_id],seed,counts)
            self.seed=seed;self.days=0;self.history=[]
            self._check()
        else:
            super().__init__(seed=seed,governance=governance,counts=counts,
                             digestion=digestion,predator_scavenging=predator_scavenging)
    def report(self):
        out=super().report()
        out['mate_search']='opt_in' if self.mate_search else 'disabled'
        if self.mate_search:out['mate_search_fluxes']={k:v for k,v in self.bridge.fluxes.items() if k.startswith('mate_search_')}
        return out
