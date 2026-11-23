"""Cycle075: opt-in energy-deficit guard, with physical-Book flux accounting.

A starving herbivore may prioritize feeding over exploration only when there is
locally accessible plant mass and chemical energy. Danger/rest are preserved.
"""
from collections import Counter
from adaptive_feeding_02174 import AdaptiveFeedingBridge274
from species_life_02115 import PROFILES

class EnergyGuardBridge275(AdaptiveFeedingBridge274):
    def evaluate_needs(self,a):
        action,hunger,danger=super().evaluate_needs(a)
        if not getattr(self,'energy_guard',False) or a.species not in ('field_mouse','meadow_grazer','forest_browser') or a.stage=='dependent':
            return action,hunger,danger
        p=PROFILES[a.species]
        demand=.001*(.5+.5*p.metabolism/.1)
        reserve=self.book.energy[self.physical.reserve(a)]
        self.energy_guard_metrics['evaluations']+=1
        if reserve>=2*demand or danger or action in ('feed','hide','rest'):
            return action,hunger,danger
        if self.book.mass[self.physical.plant(a)]<=.04 or self.book.energy[self.physical.chem(a)]<=.00032:
            self.energy_guard_metrics['food_unavailable']+=1
            return action,hunger,danger
        self.energy_guard_metrics['prioritized_feeds']+=1
        old=self.needs_last.get(a.id)
        if old is not None:self.needs_choices[f'{a.species}:{old}']-=1
        self.needs_choices[f'{a.species}:feed']+=1
        self.needs_last[a.id]='feed'
        return 'feed',hunger,danger
    def _metabolize(self,a):
        before=self.book.energy[self.physical.reserve(a)]
        result=super()._metabolize(a)
        if getattr(self,'energy_guard',False):
            after=self.book.energy[self.physical.reserve(a)]
            self.energy_guard_metrics['metabolic_paid_micro']+=round(max(0,before-after)*1e6)
            if after<.0005:self.energy_guard_metrics['critically_low_reserve_days']+=1
        return result
