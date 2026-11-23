"""Cycle042 opt-in 5-habitat WORLD-023 economy + RSW-K family investment.

Default config preserves Cycle041 four-habitat observational map and family
behavior. Five-habitat resources split existing Book stocks, no new economy.
"""
from spatial_map_02137 import Unified240
from five_habitat_02142 import FiveHabitatRunner, add_funded_floodplain, FIFTH
from knowledge_family_02142 import KnowledgeFamilyBridge242

class Unified242(Unified240):
    def __init__(self,seed=9711,governance='collective',counts=None,*,grid_size=8,
                 five_habitats=False,family_benefits=False,resource_aware_family=False,
                 colonize_floodplain=True):
        if resource_aware_family and not family_benefits:
            raise ValueError('resource-aware investment requires existing family benefits')
        self.seed=seed;self.days=0;self.history=[]
        self.five_habitats=bool(five_habitats)
        self.resource_aware_family=bool(resource_aware_family)
        self.founding_families=True
        self.family_benefits=bool(family_benefits)
        self.predator_energy_adaptation=True
        self.digestion=True
        self.predator_scavenging=True
        self.mate_search=True
        self.mouse_hysteresis=False
        self.initial_hound_dispersion=False
        self.host=FiveHabitatRunner(seed=seed,governance=governance)
        tree=self.host.sim.world_trees.worlds[self.host.tree_id]
        if self.five_habitats:
            add_funded_floodplain(tree)
        self.bridge=KnowledgeFamilyBridge242(tree,seed,counts,grid_size=grid_size,
                    family_benefits=family_benefits,
                    resource_aware_family=resource_aware_family,
                    mate_search=self.mate_search,mouse_hysteresis=self.mouse_hysteresis,
                    initial_hound_dispersion=self.initial_hound_dispersion,
                    predator_scavenging=self.predator_scavenging)
        self.floodplain_colonizations=0
        if self.five_habitats and colonize_floodplain:
            self._funded_floodplain_families()
        self._check()

    def _funded_floodplain_families(self):
        """Seed 2 existing grassland pairs into floodplain with funded travel."""
        for species in ('field_mouse','meadow_grazer'):
            pairs=[(f,m) for _,(f,m) in sorted(self.bridge.family_pairs.items())
                   if self.bridge.actors[f].species==species]
            if not pairs:continue
            f,m=pairs[-1]
            for uid in (f,m):
                animal=self.bridge.actors[uid]
                before=animal.habitat
                if FIFTH not in self.bridge.tree.habitats[before].neighbors:
                    raise ValueError('cannot colonize nonadjacent floodplain')
                cost=self.bridge.TRAVEL_COST
                account=self.bridge.physical.reserve(animal)
                if self.host.book.energy[account] < cost + .0005:
                    raise ValueError('insufficient physical energy for initial colonization')
                self.host.book.move(energy=[(account,'environment:heat',cost)])
                animal.habitat=FIFTH
                self.bridge._log('migration',actor=uid,species=species,
                    from_habitat=before,to_habitat=FIFTH,
                    energy_cost=cost,reason='funded_initial_family_colonization')
                self.floodplain_colonizations+=1
        self.bridge.sync_positions()

    def report(self):
        out=super().report()
        out['habitats']=list(self.bridge.tree.habitats)
        out['habitat_balances']={p:{
            'plant':round(self.host.book.mass[self.bridge.tree.acct('plant',p)],8),
            'soil':round(self.host.book.mass[self.bridge.tree.acct('soil',p)],8),
            'water':round(self.host.book.mass[self.bridge.tree.acct('water',p)],8),
            'chemical_energy':round(self.host.book.energy[self.bridge.tree.acct('chem',p)],8)}
            for p in self.bridge.tree.habitats}
        out['five_habitats']=self.five_habitats
        out['resource_aware_family']=self.resource_aware_family
        out['floodplain_colonizations']=self.floodplain_colonizations
        out['family_knowledge']=dict(self.bridge.family_knowledge_metrics)
        return out
