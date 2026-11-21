"""Cycle010 unified experimental host; preserves WORLD-023 clock and Book."""
from unified_02122 import Unified222
from habitat_bridge_02123 import HabitatBridge223

class Unified223(Unified222):
    def __init__(self,seed=9711,governance='collective',counts=None,
                 digestion=False,predator_scavenging=False,mate_search=False,
                 mouse_hysteresis=False,initial_hound_dispersion=False):
        self.mouse_hysteresis=bool(mouse_hysteresis)
        self.initial_hound_dispersion=bool(initial_hound_dispersion)
        if (mate_search or mouse_hysteresis or initial_hound_dispersion) and not digestion:
            raise ValueError('opt-in biological adapters require digestion Book interface')
        if not any((mate_search,mouse_hysteresis,initial_hound_dispersion)):
            super().__init__(seed=seed,governance=governance,counts=counts,
                             digestion=digestion,predator_scavenging=predator_scavenging,
                             mate_search=mate_search)
        else:
            from living_tree_runner import LivingTreeRunner
            self.digestion=True
            self.predator_scavenging=bool(predator_scavenging)
            self.mate_search=bool(mate_search)
            self.host=LivingTreeRunner(seed=seed,governance=governance)
            self.bridge=HabitatBridge223(
                self.host.sim.world_trees.worlds[self.host.tree_id],seed,counts,
                mate_search=mate_search,mouse_hysteresis=mouse_hysteresis,
                initial_hound_dispersion=initial_hound_dispersion,
                predator_scavenging=predator_scavenging)
            self.seed=seed;self.days=0;self.history=[]
            self._check()

    def report(self):
        result=super().report()
        result['mouse_hysteresis']='opt_in' if self.mouse_hysteresis else 'disabled'
        result['initial_hound_dispersion']='opt_in' if self.initial_hound_dispersion else 'disabled'
        if isinstance(self.bridge,HabitatBridge223):
            result['crossagent_fluxes']=dict(self.bridge.integration_fluxes)
        return result
