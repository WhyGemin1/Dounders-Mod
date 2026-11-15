"""Opt-in juvenile forage priority: change decisions, not observations or resource supply."""
from reproduction_02181 import ReproductiveBridge281, HERB
from species_life_02115 import NEEDS, PROFILES

class ReproductiveBridge282(ReproductiveBridge281):
    def _metabolize(self,a):
        if not getattr(self,'juvenile_foraging',False) or a.species not in HERB or a.stage!='juvenile':
            return super()._metabolize(a)
        # Post-weaning energy retention: reduced locomotor expenditure, but
        # reduced recovery, with every joule still debited to environmental heat.
        threat=any(x.alive and x.species=='ridge_hound' and x.habitat==a.habitat
                   for x in self.actors.values())
        if threat:return super()._metabolize(a)
        p=PROFILES[a.species];reserve=self.physical.reserve(a)
        demand=.001*(.5+.5*p.metabolism/.1)*.40
        burn=min(self.book.energy[reserve],demand)
        if burn:self.book.move(energy=[(reserve,'environment:heat',burn)])
        a.condition=min(1.,a.condition+.001) if burn>=.8*demand else max(0.,a.condition-.035)

    def evaluate_needs(self,a):
        action,hunger,danger=super().evaluate_needs(a)
        if not getattr(self,'juvenile_foraging',False):
            return action,hunger,danger
        if a.species not in HERB or a.stage!='juvenile' or danger:
            return action,hunger,danger
        reserve=self.book.energy[self.physical.reserve(a)]
        target=.035*NEEDS[a.species][7]
        if reserve>=target*.80:
            return action,hunger,danger
        # Feed only if a *real* existing edible mass stock is present locally.
        plant=self.book.mass[self.physical.plant(a)]>.04
        seeds=self.book.mass[f'forage:seeds:{a.habitat}']>=.0004
        browse=self.book.mass[f'forage:browse:{a.habitat}']>=.0004
        if plant or seeds or browse:
            return 'feed',hunger,danger
        return action,hunger,danger
