"""Cycle098 opt-in juvenile threat escape; never modifies canonical schedulers."""
from integrated_02196 import Unified296, ConservativeBridge296
from reproduction_02183 import HERB

class RefugeBridge298(ConservativeBridge296):
    def _migrate(self, actor, decision=None):
        if not getattr(self, 'juvenile_refuge', False) or actor.species not in HERB or actor.stage != 'juvenile':
            return super()._migrate(actor, decision)
        here = actor.habitat
        threats = [x for x in self.actors.values() if x.alive and x.species == 'ridge_hound' and x.habitat == here]
        if not threats:
            return super()._migrate(actor, decision)
        reserve = self.physical.reserve(actor)
        if self.book.energy[reserve] < self.TRAVEL_COST + .004:
            return False
        safe = [h for h in self.tree.habitats[here].neighbors if not any(
            x.alive and x.species == 'ridge_hound' and x.habitat == h for x in self.actors.values())]
        if not safe:
            return False
        def food(h):
            stock = sum(self.book.mass.get(f'forage:{kind}:{h}', 0.) for kind in ('browse','seeds'))
            competitors = sum(x.alive and x.species in HERB and x.habitat == h for x in self.actors.values())
            return stock / max(1, competitors + 1)
        best = max(safe, key=lambda h:(food(h), h))
        self.book.move(energy=[(reserve,'environment:heat',self.TRAVEL_COST)])
        actor.habitat = best
        actor.hidden = False
        self._log('migration',actor=actor.id,species=actor.species,from_habitat=here,
                  to_habitat=best,reason='juvenile_predator_refuge',energy_cost=self.TRAVEL_COST)
        return True

class Unified298(Unified296):
    def __init__(self,*args,juvenile_refuge=False,**kwargs):
        super().__init__(*args,**kwargs)
        self.bridge.__class__=RefugeBridge298
        self.bridge.juvenile_refuge=bool(juvenile_refuge)
        self.juvenile_refuge=bool(juvenile_refuge)
        self._check()
