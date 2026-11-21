"""Opt-in juvenile natal foraging: finite-energy habitat selection and predator avoidance."""
from reproduction_02182 import ReproductiveBridge282, HERB
from species_life_02115 import PROFILES

class ReproductiveBridge283(ReproductiveBridge282):
    def _migrate(self,a,decision=None):
        if not getattr(self,'natal_foraging',False) or a.species not in HERB or a.stage!='juvenile':
            return super()._migrate(a,decision)
        here=a.habitat
        neighbors=tuple(self.tree.habitats[here].neighbors)
        reserve=self.physical.reserve(a)
        if not neighbors or self.book.energy[reserve]<self.TRAVEL_COST+.002:
            return super()._migrate(a,decision)
        def forage(h):
            plant=self.book.mass[self.tree.acct('plant',h)]
            browse=self.book.mass[f'forage:browse:{h}']
            seeds=self.book.mass[f'forage:seeds:{h}']
            predator=sum(x.alive and x.species=='ridge_hound' and x.habitat==h for x in self.actors.values())
            return plant+2*(browse+seeds)-.25*predator
        best=max(neighbors,key=lambda h:(forage(h),h))
        if forage(best)>forage(here)+.10:
            self.book.move(energy=[(reserve,'environment:heat',self.TRAVEL_COST)])
            a.habitat=best;a.hidden=False
            return True
        return super()._migrate(a,decision)
