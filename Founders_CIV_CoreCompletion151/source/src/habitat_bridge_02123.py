"""Cycle010: one-Book opt-in integration of adjacent mate cues and mouse satiation.

Inherits the existing v0.21.22 embodied-food and native-Tree adapter.
No parallel population clock or physical resource ledger is added.
"""
from collections import Counter
from mate_search_02122 import HabitatBridge222
from digestion_02120 import HabitatBridge220
from species_life_02115 import PROFILES, MASS_SCALE, YEAR, PREY
from stateful_mouse_needs_02123 import mouse_hunger_transition

class HabitatBridge223(HabitatBridge222):
    def __init__(self, tree, seed=9711, counts=None, *,
                 mate_search=False, mouse_hysteresis=False,
                 initial_hound_dispersion=False, predator_scavenging=False):
        super().__init__(tree, seed=seed, counts=counts)
        self.mate_search_enabled = bool(mate_search)
        self.predator_scavenging_enabled = bool(predator_scavenging)
        self.mouse_hysteresis_enabled = bool(mouse_hysteresis)
        self.hound_dispersion_enabled = bool(initial_hound_dispersion)
        self.mouse_hungry = {}
        self.integration_fluxes = Counter()
        if self.hound_dispersion_enabled:
            self._funded_initial_hound_dispersion()

    def _funded_initial_hound_dispersion(self):
        """Controlled initial spatial variation: no free teleport/energy.

        Move alternate starting hounds to a directly adjacent habitat, paying
        the same physical travel charge as ordinary migration. This is an
        explicit experimental initial-condition arm, not an adaptive benefit.
        """
        hounds = [a for a in self.actors.values() if a.alive and a.species == 'ridge_hound']
        for index, animal in enumerate(hounds):
            if index % 2 == 0:  # leave alternating hounds at their original home
                continue
            neighbor_list = tuple(sorted(self.tree.habitats[animal.habitat].neighbors))
            if not neighbor_list:
                continue
            source = self.physical.reserve(animal)
            cost = self.TRAVEL_COST
            if self.book.energy[source] < cost + .0005:
                self.integration_fluxes['dispersion_unaffordable'] += 1
                continue
            before=animal.habitat
            destination=neighbor_list[0]
            self.book.move(energy=[(source, 'environment:heat', cost)])
            animal.habitat=destination
            self.integration_fluxes['dispersion_moves'] += 1
            self.integration_fluxes['dispersion_energy'] += cost
            self._log('migration', actor=animal.id,species=animal.species,
                      from_habitat=before,to_habitat=destination,
                      energy_cost=cost,reason='experimental_initial_dispersion')

    def _migrate(self,animal,decision=None):
        base_migrate = super(HabitatBridge222,self)._migrate
        if not self.mate_search_enabled:
            # Existing v0.21.21 policy, no surprise mate-cue path.
            return base_migrate(animal,decision)
        if animal.alive and animal.species in PREY:
            p=PROFILES[animal.species]
            if not (p.breeding[0] <= self.day % YEAR <= p.breeding[1]):
                self.integration_fluxes['mate_gate_out_of_season'] += 1
            elif animal.stage != 'adult':
                self.integration_fluxes['mate_gate_not_adult'] += 1
            elif animal.condition < .65:
                self.integration_fluxes['mate_gate_low_condition'] += 1
            elif (animal.sex == 'F' and
                  self.book.mass[self.physical.maternal(animal)] < p.birth_cost * MASS_SCALE):
                # Correct v0.21.22's .012 gate, which permitted mate travel
                # before the actual life-history conception stock .1*cost.
                self.integration_fluxes['mate_gate_maternal_shortfall'] += 1
                return base_migrate(animal,decision)
            else:
                self.integration_fluxes['mate_gate_physically_eligible'] += 1
        return super()._migrate(animal,decision)

    def _hunt(self,animal):
        # Mate-cue inheritance must not silently enable scavenging when off.
        if self.predator_scavenging_enabled:
            return super()._hunt(animal)
        return HabitatBridge220._hunt(self,animal)

    def _feed_herbivore(self,animal):
        if not self.mouse_hysteresis_enabled or animal.species != 'field_mouse':
            return super()._feed_herbivore(animal)
        reserve=self.book.energy[self.physical.reserve(animal)]
        old=self.mouse_hungry.get(animal.id, reserve <= .035)
        now=mouse_hunger_transition(reserve,old)
        self.mouse_hungry[animal.id]=now
        self.integration_fluxes['mouse_feeding_opportunities'] += 1
        if now != old:
            self.integration_fluxes['mouse_hunger_transitions'] += 1
            self._log('mouse_hunger_transition',actor=animal.id,habitat=animal.habitat,
                      hungry=now,reserve=reserve)
        if not now:
            self.integration_fluxes['mouse_satiated_skips'] += 1
            return False
        result=super()._feed_herbivore(animal)
        if result:
            self.integration_fluxes['mouse_funded_meals'] += 1
        return result

    def census(self):
        data=super().census()
        data['crossagent_fluxes']={k:round(v,9) for k,v in sorted(self.integration_fluxes.items())}
        data['mouse_hunger_states']={k:bool(v) for k,v in sorted(self.mouse_hungry.items())}
        return data
