"""Cycle039 opt-in founding families + bounded parental investment."""
from unified_02135 import Unified238
from family_pair_02136 import HabitatBridge239

class Unified239(Unified238):
    def __init__(self,seed=9711,governance='collective',counts=None,
                 digestion=True,predator_scavenging=True,mate_search=True,
                 mouse_hysteresis=False,initial_hound_dispersion=False,
                 predator_energy_adaptation=True,founding_families=False,
                 family_benefits=True):
        self.founding_families=bool(founding_families)
        self.family_benefits=bool(family_benefits)
        if not founding_families:
            return super().__init__(seed=seed,governance=governance,counts=counts,
                digestion=digestion,predator_scavenging=predator_scavenging,
                mate_search=mate_search,mouse_hysteresis=mouse_hysteresis,
                initial_hound_dispersion=initial_hound_dispersion,
                predator_energy_adaptation=predator_energy_adaptation)
        if not (digestion and predator_energy_adaptation):
            raise ValueError('founding families require funded digestion and energy adapter')
        from living_tree_runner import LivingTreeRunner
        self.predator_energy_adaptation=True
        self.digestion=True
        self.predator_scavenging=bool(predator_scavenging)
        self.mate_search=bool(mate_search)
        self.mouse_hysteresis=bool(mouse_hysteresis)
        self.initial_hound_dispersion=bool(initial_hound_dispersion)
        self.host=LivingTreeRunner(seed=seed,governance=governance)
        self.bridge=HabitatBridge239(self.host.sim.world_trees.worlds[self.host.tree_id],seed,counts,
            family_benefits=family_benefits,
            mate_search=mate_search,mouse_hysteresis=mouse_hysteresis,
            initial_hound_dispersion=initial_hound_dispersion,
            predator_scavenging=predator_scavenging)
        self.seed=seed;self.days=0;self.history=[]
        self._check()

    def report(self):
        result=super().report()
        result['founding_families']='opt_in' if self.founding_families else 'disabled'
        result['family_benefits']='enabled' if self.founding_families and self.family_benefits else 'disabled'
        if self.founding_families:
            result['family_metrics']=self.bridge.census()['family_fluxes']
        return result
