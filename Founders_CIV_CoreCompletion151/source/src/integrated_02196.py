"""Cycle096 experimental conservative migration; never modifies canonical schedulers."""
from integrated_02195 import Unified295, AccessibleBridge295
from reproduction_02183 import HERB

class ConservativeBridge296(AccessibleBridge295):
    def _migrate(self, actor, decision=None):
        if not getattr(self, 'conservative_access', False) or actor.species not in HERB:
            return super()._migrate(actor, decision)
        # Dependent offspring remain in their natal habitat. Avoid the unrestricted
        # fallback for this experimental arm: a rejected journey is a stay decision.
        if actor.stage == 'dependent':
            return False
        here = actor.habitat
        reserve = self.physical.reserve(actor)
        energy = self.book.energy[reserve]
        cost = self.TRAVEL_COST
        # Require a substantial reserve beyond the travel fee; low-energy
        # animals must preserve energy for metabolism and feeding.
        if energy < max(0.03, 6 * cost):
            return False
        def score(h):
            forage = sum(self.book.mass.get(f'forage:{k}:{h}', 0.) for k in ('browse', 'seeds'))
            competitors = sum(x.alive and x.species in HERB and x.habitat == h for x in self.actors.values())
            predators = sum(x.alive and x.species == 'ridge_hound' and x.habitat == h for x in self.actors.values())
            return forage / max(1, competitors + (h != here)) - 0.25 * predators
        origin = score(here)
        options = [h for h in self.tree.habitats[here].neighbors if
                   score(h) > origin + 0.05 and
                   not any(x.alive and x.species == 'ridge_hound' and x.habitat == h for x in self.actors.values())]
        if not options:
            return False
        best = max(options, key=lambda h: (score(h), h))
        self.book.move(energy=[(reserve, 'environment:heat', cost)])
        actor.habitat = best
        actor.hidden = False
        self._log('migration', actor=actor.id, species=actor.species,
                  from_habitat=here, to_habitat=best,
                  reason='conservative_net_access', energy_cost=cost)
        return True

class Unified296(Unified295):
    def __init__(self, *args, conservative_access=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.bridge.__class__ = ConservativeBridge296
        self.bridge.conservative_access = bool(conservative_access)
        self.conservative_access = bool(conservative_access)
        self._check()
