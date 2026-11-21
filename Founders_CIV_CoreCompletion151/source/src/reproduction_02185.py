"""Cycle085 experimental: juvenile compensatory grazing with finite food and energy.
Juveniles may take a second meal only after a successful first meal. Both
meals use the existing Book-funded _feed_stock path; no resource creation.
"""
from reproduction_02184 import ReproductiveBridge284, HERB

class ReproductiveBridge285(ReproductiveBridge284):
    def _feed_herbivore(self, animal):
        first = super()._feed_herbivore(animal)
        if (first and getattr(self, 'compensatory_grazing', False)
                and animal.species in HERB and animal.stage == 'juvenile'):
            # This costs real plant/browse/seed stocks and habitat chemical energy.
            super()._feed_herbivore(animal)
        return first
