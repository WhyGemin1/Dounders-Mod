"""A-021 opt-in adjacency-only, energy-funded hound mate search."""
from digestion_02121 import HabitatBridge221
from species_life_02115 import PROFILES, PREY, YEAR

MATE_SEARCH_COST_FACTOR=1.35
class HabitatBridge222(HabitatBridge221):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.mate_search_enabled=True

    def _migrate(self,a,decision=None):
        if a.species in PREY and a.stage=='adult' and a.alive:
            profile=PROFILES[a.species]
            phase=self.day%YEAR
            if profile.breeding[0]<=phase<=profile.breeding[1] and a.condition>=.65:
                reserve=self.physical.reserve(a)
                cost=self.TRAVEL_COST*MATE_SEARCH_COST_FACTOR
                if self.book.energy[reserve]<cost+.012:
                    self.fluxes['mate_search_insufficient_energy']+=1
                elif a.sex=='F' and (a.pregnant_until is not None or
                    self.book.mass[self.physical.maternal(a)]<profile.birth_cost*.012):
                    self.fluxes['mate_search_ineligible']+=1
                elif any(x.alive and x.species==a.species and x.sex!=a.sex
                         and x.stage=='adult' and x.condition>=.65 and
                         x.habitat==a.habitat for x in self.actors.values()):
                    self.fluxes['mate_search_local_encounter']+=1
                else:
                    here=a.habitat
                    adjacent=tuple(self.tree.habitats[here].neighbors)
                    # Read only direct neighbor cues; never consult distant habitats.
                    targets=[h for h in adjacent if any(x.alive and x.id!=a.id
                        and x.species==a.species and x.sex!=a.sex
                        and x.stage=='adult' and x.condition>=.65
                        and x.habitat==h for x in self.actors.values())]
                    if targets:
                        # Travel is risky, and an eligible cue is not a guaranteed encounter.
                        self.fluxes['mate_search_cues']+=1
                        if self.rng.random()<.65:
                            dest=self.rng.choice(targets)
                            self.book.move(energy=[(reserve,'environment:heat',cost)])
                            a.habitat=dest;a.hidden=False
                            self.fluxes['mate_search_moves']+=1
                            self.fluxes['mate_search_travel_energy']+=cost
                            self._log('migration',actor=a.id,species=a.species,
                                      from_habitat=here,to_habitat=dest,
                                      reason='adjacent_mate_cue',energy_cost=cost)
                            return True
                        self.fluxes['mate_search_abandoned']+=1
                    else:
                        self.fluxes['mate_search_no_adjacent_cue']+=1
        return super()._migrate(a,decision)
