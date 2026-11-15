"""Opt-in, physically conserved metabolic economy: low-reserve animals conserve energy.

No accounts or observation channels added.  Conservation is a reduced transfer
from animal reserve to environmental heat, not an energy credit.
"""
from behavior_02178 import UnifiedBehaviorBridge278
from species_life_02115 import PROFILES, NEEDS

class EnergyBudgetBridge279(UnifiedBehaviorBridge278):
    def _metabolize(self,a):
        if not getattr(self,'energy_budget',False):
            return super()._metabolize(a)
        p=PROFILES[a.species]
        reserve=self.physical.reserve(a)
        available=self.book.energy[reserve]
        nominal=.001*(.5+.5*p.metabolism/.1)
        # In the absence of immediate predation, an animal with less than five
        # daily metabolic budgets enters a low-activity conservation mode.
        threat=(a.species not in ('ridge_hound','carrion_bird') and
                any(x.alive and x.habitat==a.habitat and x.species=='ridge_hound'
                    for x in self.actors.values()))
        conserving=available<5*nominal and not threat
        demand=nominal*(.65 if conserving else 1.)
        burn=min(available,demand)
        if burn>0:self.book.move(energy=[(reserve,'environment:heat',burn)])
        # Reduced expenditure also slows recovery; no free health gain.
        if burn>=.8*demand:
            a.condition=min(1.,a.condition+(.003 if conserving else .007))
        else:
            a.condition=max(0.,a.condition-.035)
