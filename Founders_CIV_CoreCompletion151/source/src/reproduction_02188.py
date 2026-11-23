"""Cycle088: dependent juvenile nutrition funded by maternal reserve and biomass."""
from reproduction_02187 import ReproductiveBridge287
from species_life_02115 import PROFILES

class ReproductiveBridge288(ReproductiveBridge287):
    def _care(self, parent, episode='primary'):
        super()._care(parent, episode)
        if not getattr(self, 'dependent_nutrition', False) or parent.sex != 'F':
            return
        ph=self.physical; book=self.book
        for child in list(self.actors.values()):
            if not (child.alive and child.stage=='dependent' and parent.id in child.caregiver_ids
                    and child.habitat==parent.habitat):
                continue
            # Strict finite maternal transfer: mother retains minimum survival reserve.
            available=max(0.,book.energy[ph.reserve(parent)]-.008)
            target=max(0.,.018-book.energy[ph.reserve(child)])
            energy=min(.0012,available,target)
            if energy>1e-12:
                book.move(energy=[(ph.reserve(parent),ph.reserve(child),energy)])
            # Maternal stock is pre-funded by feeding; it cannot be minted for growth.
            mass=min(.00045,max(0.,book.mass[ph.maternal(parent)]-.002),
                     max(0.,PROFILES[child.species].adult_mass()*.35-book.mass[ph.live(child)]))
            if mass>1e-12:
                ph.convert([(ph.maternal(parent),ph.live(child),mass)])
            if energy>0 or mass>0:
                self._log('dependent_nutrition',actor=parent.id,child=child.id,energy=energy,mass=mass)
