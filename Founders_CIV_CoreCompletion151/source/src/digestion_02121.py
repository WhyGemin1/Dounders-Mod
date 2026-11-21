"""Cycle008: optional, physically funded opportunistic predator scavenging.

One WORLD-023 Book. Hounds choose an existing carcass only when accessible
energy offers more than the direct modeled strike cost. No free meals, no
new resource pool, no guarantee that predators survive or reproduce.
"""
from digestion_02120 import HabitatBridge220, CARRION_DIGESTIBILITY, HUNT_COST
from species_life_02115 import PROFILES, PREY
SCAVENGE_HANDLING_COST=HUNT_COST*.30

class HabitatBridge221(HabitatBridge220):
    def _hunt(self,a):
        if a.species not in PREY:
            return super()._hunt(a)
        carrion=self.carrion(a.habitat)
        mass=self.book.mass[carrion]
        energy=self.book.energy[self.physical.carrion_energy(a.habitat)]
        q=min(PROFILES[a.species].intake*.012,mass)
        # Book energy is an actual stock, not a proxy for edible biomass.
        potential=energy*(q/mass)*CARRION_DIGESTIBILITY if mass>0 else 0.
        reserve=self.book.energy[self.physical.reserve(a)]
        local_prey=any(x.alive and x.species in PREY[a.species]
                       and x.habitat==a.habitat for x in self.actors.values())
        # Reserve urgency or absence of local prey can make scavenging viable.
        if (q>=.0004 and potential>SCAVENGE_HANDLING_COST
                and reserve>SCAVENGE_HANDLING_COST+.0005
                and (not local_prey or reserve<.012)):
            before=reserve
            if self._feed_stock(a,carrion,'predator_carrion'):
                # Scavenging is cheaper than a strike, but handling is not free.
                self.book.move(energy=[(self.physical.reserve(a),'environment:heat',
                                        SCAVENGE_HANDLING_COST)])
                gained=self.book.energy[self.physical.reserve(a)]-before
                self.fluxes['predator_scavenge_handling_cost']+=SCAVENGE_HANDLING_COST
                self.fluxes['predator_scavenge_energy_gained']+=gained
                self.fluxes['predator_scavenge_meals']+=1
                self._log('predator_scavenge',actor=a.id,habitat=a.habitat,
                          energy_gain=gained,carcass_mass=q,handling_cost=SCAVENGE_HANDLING_COST)
                return True
        return super()._hunt(a)
