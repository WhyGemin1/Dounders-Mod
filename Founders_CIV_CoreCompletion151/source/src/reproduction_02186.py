"""Experimental juvenile maturation: use existing forage for growth, not free reserves."""
from reproduction_02185 import ReproductiveBridge285, HERB
from species_life_02115 import PROFILES

class ReproductiveBridge286(ReproductiveBridge285):
    def evaluate_needs(self, a):
        action,hunger,danger=super().evaluate_needs(a)
        if not getattr(self,'maturation_feeding',False) or a.species not in HERB or a.stage!='juvenile' or danger:
            return action,hunger,danger
        # Feed only when an edible physical stock exists; no new resource account.
        stock=(self.book.mass[self.physical.plant(a)] +
               self.book.mass[f'forage:seeds:{a.habitat}'] +
               self.book.mass[f'forage:browse:{a.habitat}'])
        if stock>.045 and self.book.energy[self.physical.reserve(a)]<.06:
            return 'feed',hunger,danger
        return action,hunger,danger

    def _metabolize(self,a):
        # Reuse tested energy-budget implementation, no new energy channels.
        return super()._metabolize(a)
