"""Opt-in, finite-Book post-independence family support experiment.

Preserves Cycle136 dependent feeding and all species maturity thresholds.
Juveniles first use ordinary autonomous foraging; when reserves are critical,
co-located surviving caregivers may provide a meal at their own energy cost.
"""
from collections import Counter
from juvenile_support_cycle136 import JuvenileSupportBridge136, enable_assisted_feeding, ASSIST_CHILD_RESERVE_TARGET
from species_life_02115 import PROFILES

JUVENILE_EMERGENCY_RESERVE = ASSIST_CHILD_RESERVE_TARGET * 0.5

class JuvenileTransitionBridge138(JuvenileSupportBridge136):
    def evaluate_needs(self, a):
        if (a.alive and a.generation >= 1 and a.stage == 'juvenile'
                and a.age < PROFILES[a.species].maturity):
            self.juvenile_transition_metrics['opportunities'] += 1
            if self.book.energy[self.physical.reserve(a)] < JUVENILE_EMERGENCY_RESERVE:
                before = self.juvenile_support_metrics['successful_meals']
                self._try_assisted_feed(a)
                if self.juvenile_support_metrics['successful_meals'] > before:
                    self.juvenile_transition_metrics['successful_emergency_meals'] += 1
        return super().evaluate_needs(a)

def enable_transition_support(sim):
    enable_assisted_feeding(sim)
    if type(sim.bridge) is not JuvenileSupportBridge136:
        raise TypeError('expected Cycle136 opt-in bridge')
    sim.bridge.__class__ = JuvenileTransitionBridge138
    sim.bridge.juvenile_transition_metrics = Counter()
    return sim
