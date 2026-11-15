"""Cycle084 opt-in lactation and juvenile growth, finite Book transfers only.

Dependent energy is supplied by living caregivers, never created. A caregiver
retains its own maintenance reserve; weaning juveniles eat existing forage.
"""
from reproduction_02183 import ReproductiveBridge283, HERB
from species_life_02115 import PROFILES

class ReproductiveBridge284(ReproductiveBridge283):
    def _care(self, a, episode='primary'):
        super()._care(a, episode)
        if not getattr(self, 'lactation_growth', False) or a.species not in HERB or a.stage != 'adult':
            return
        donor = self.physical.reserve(a)
        profile = PROFILES[a.species]
        # Parents cannot subsidize offspring by spending their own survival reserve.
        floor = .006 + 4 * .001 * (.5 + .5 * profile.metabolism / .1)
        children = [c for c in self.actors.values() if c.alive and c.species == a.species
                    and c.stage == 'dependent' and a.id in c.caregiver_ids
                    and c.habitat == a.habitat]
        for child in children:
            receiver = self.physical.reserve(child)
            amount = min(.0025, max(0., self.book.energy[donor] - floor),
                         max(0., .012 - self.book.energy[receiver]))
            if amount > 1e-12:
                self.book.move(energy=[(donor, receiver, amount)])

    def evaluate_needs(self, a):
        action, hunger, danger = super().evaluate_needs(a)
        if not getattr(self, 'lactation_growth', False) or a.species not in HERB or a.stage != 'juvenile' or danger:
            return action, hunger, danger
        # A recently weaned juvenile eats real forage to finance growth.
        if self.book.energy[self.physical.reserve(a)] < .035 and (
            self.book.mass[self.physical.plant(a)] > .04 or
            self.book.mass[f'forage:seeds:{a.habitat}'] >= .0004 or
            self.book.mass[f'forage:browse:{a.habitat}'] >= .0004
        ):
            return 'feed', hunger, danger
        return action, hunger, danger
