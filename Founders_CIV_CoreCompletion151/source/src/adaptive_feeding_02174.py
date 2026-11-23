"""Cycle074: opt-in local feeding priority with ledger-neutral diagnostics.

The existing scheduler performs all feeding and physical transactions. This
policy changes only the selected need when locally funded food is available.
"""
from collections import Counter
from resource_access_02170 import ResourceAccessBridge270

class AdaptiveFeedingBridge274(ResourceAccessBridge270):
    def evaluate_needs(self, animal):
        action, hunger, danger = super().evaluate_needs(animal)
        if not getattr(self, 'adaptive_feeding', False) or animal.species not in ('field_mouse','meadow_grazer','forest_browser') or animal.stage == 'dependent':
            return action, hunger, danger
        reserve = self.book.energy[self.physical.reserve(animal)]
        plant = self.book.mass[self.physical.plant(animal)]
        chem = self.book.energy[self.physical.chem(animal)]
        self.feeding_metrics['assessments'] += 1
        if reserve >= .025:
            self.feeding_metrics['reserve_sufficient'] += 1
            return action, hunger, danger
        if plant <= .04:
            self.feeding_metrics['plant_unavailable'] += 1
            return action, hunger, danger
        if chem <= .00032:
            self.feeding_metrics['chemical_energy_unavailable'] += 1
            return action, hunger, danger
        if action in ('feed','rest','hide'):
            return action, hunger, danger
        # Preserve danger responses, reproductive decisions, and physical costs.
        if danger:
            self.feeding_metrics['danger_deferrals'] += 1
            return action, hunger, danger
        self.feeding_metrics['prioritized_feed'] += 1
        prior = self.needs_last.get(animal.id)
        if prior is not None:
            self.needs_choices[f'{animal.species}:{prior}'] -= 1
        self.needs_choices[f'{animal.species}:feed'] += 1
        self.needs_last[animal.id] = 'feed'
        return 'feed', hunger, danger

    def _feed_stock(self, animal, source, kind):
        before = self.book.energy[self.physical.reserve(animal)]
        result = super()._feed_stock(animal, source, kind)
        if getattr(self, 'adaptive_feeding', False):
            self.feeding_metrics['feeding_attempts'] += 1
            if result:
                self.feeding_metrics['successful_meals'] += 1
                self.feeding_metrics['reserve_energy_gain_micro'] += round(max(0.,self.book.energy[self.physical.reserve(animal)]-before)*1e6)
            else:
                self.feeding_metrics['failed_meals'] += 1
        return result
