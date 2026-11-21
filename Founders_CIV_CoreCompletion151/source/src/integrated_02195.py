"""Cycle095 opt-in finite-energy forage-access movement, preserving both schedulers."""
from integrated_02194 import Unified294
from reproduction_02183 import ReproductiveBridge283, HERB

class AccessibleBridge295(ReproductiveBridge283):
    def _migrate(self, actor, decision=None):
        if not getattr(self, 'funded_access', False) or actor.species not in HERB or actor.stage == 'dependent':
            return super()._migrate(actor, decision)
        here=actor.habitat
        neighbors=self.tree.habitats[here].neighbors
        reserve=self.physical.reserve(actor)
        if self.book.energy[reserve] < self.TRAVEL_COST + .002:
            return super()._migrate(actor, decision)
        def share(h):
            edible=sum(self.book.mass[f'forage:{kind}:{h}'] for kind in ('browse','seeds'))
            consumers=sum(x.alive and x.species in HERB and x.habitat==h for x in self.actors.values())
            predators=sum(x.alive and x.species=='ridge_hound' and x.habitat==h for x in self.actors.values())
            return edible/max(1,consumers+(h!=here)) - .02*predators
        if neighbors:
            best=max(neighbors,key=lambda h:(share(h),h))
            if share(best)>share(here)+.002:
                self.book.move(energy=[(reserve,'environment:heat',self.TRAVEL_COST)])
                actor.habitat=best;actor.hidden=False
                self._log('migration',actor=actor.id,species=actor.species,from_habitat=here,
                          to_habitat=best,reason='finite_edible_share',energy_cost=self.TRAVEL_COST)
                return True
        return super()._migrate(actor, decision)

class Unified295(Unified294):
    def __init__(self,*args,funded_access=False,**kwargs):
        super().__init__(*args,**kwargs)
        self.bridge.__class__=AccessibleBridge295
        self.bridge.funded_access=bool(funded_access)
        self.funded_access=bool(funded_access)
        self._check()
