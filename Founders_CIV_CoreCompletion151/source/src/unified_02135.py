"""Cycle038 opt-in physically funded energy adaptation, one host clock and Book."""
from unified_02123 import Unified223
from energy_adaptation_02135 import HabitatBridge238

class Unified238(Unified223):
    def __init__(self,seed=9711,governance='collective',counts=None,
                 digestion=False,predator_scavenging=False,mate_search=False,
                 mouse_hysteresis=False,initial_hound_dispersion=False,
                 predator_energy_adaptation=False):
        self.predator_energy_adaptation=bool(predator_energy_adaptation)
        if not self.predator_energy_adaptation:
            return super().__init__(seed=seed,governance=governance,counts=counts,
                   digestion=digestion,predator_scavenging=predator_scavenging,
                   mate_search=mate_search,mouse_hysteresis=mouse_hysteresis,
                   initial_hound_dispersion=initial_hound_dispersion)
        if not digestion:
            raise ValueError('predator energy adaptation requires funded digestion')
        from living_tree_runner import LivingTreeRunner
        self.digestion=True
        self.predator_scavenging=bool(predator_scavenging)
        self.mate_search=bool(mate_search)
        self.mouse_hysteresis=bool(mouse_hysteresis)
        self.initial_hound_dispersion=bool(initial_hound_dispersion)
        self.host=LivingTreeRunner(seed=seed,governance=governance)
        self.bridge=HabitatBridge238(self.host.sim.world_trees.worlds[self.host.tree_id],seed,counts,
                    mate_search=mate_search,mouse_hysteresis=mouse_hysteresis,
                    initial_hound_dispersion=initial_hound_dispersion,
                    predator_scavenging=predator_scavenging)
        self.seed=seed;self.days=0;self.history=[]
        self._check()

    def report(self):
        output=super().report()
        output['predator_energy_adaptation']='opt_in' if self.predator_energy_adaptation else 'disabled'
        if self.predator_energy_adaptation:
            output['predator_energy_fluxes']=dict(self.bridge.predator_energy_fluxes)
        return output
