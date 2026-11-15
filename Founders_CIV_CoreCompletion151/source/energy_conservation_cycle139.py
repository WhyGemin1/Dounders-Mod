"""Opt-in demand-responsive metabolism experiment, NOT canonical.

Biology-inspired but synthetic coefficients. Energy is paid only for maintenance
and exertion, not for making a decision. Book moves remain authoritative.
"""
from collections import Counter
from species_life_02115 import PROFILES
from juvenile_transition_cycle138 import JuvenileTransitionBridge138, enable_transition_support

# Resting expenditure cannot be zero; voluntary action is not automatically work.
MAINTENANCE_FRACTION = 0.35
EXERTION_FRACTION = 0.30
LOW_RESERVE = 0.004

class ConservationBridge139(JuvenileTransitionBridge138):
    def _metabolize(self, a):
        if not a.alive:
            return
        p = PROFILES[a.species]
        basal = .001 * (.5 + .5 * p.metabolism / .1)
        action = self.needs_last.get(a.id, 'rest')
        # Searching/hunting incurs work; feeding/mating/rest do not incur a
        # separate arbitrary action tax. Maintenance continues in all states.
        exertion = action in ('search', 'hunt', 'flee', 'travel')
        demand = basal * (MAINTENANCE_FRACTION + (EXERTION_FRACTION if exertion else 0.))
        account = self.physical.reserve(a)
        before = self.book.energy[account]
        burn = min(before, demand)
        if burn > 0:
            self.book.move(energy=[(account, 'environment:heat', burn)])
        self.conservation_metrics['maintenance_paid'] += min(burn, basal * MAINTENANCE_FRACTION)
        self.conservation_metrics['exertion_paid'] += max(0., burn - basal * MAINTENANCE_FRACTION)
        if burn >= demand * .8:
            a.condition = min(1., a.condition + (.010 if action == 'rest' else .007))
        else:
            a.condition = max(0., a.condition - .035)

    def evaluate_needs(self, a):
        action, hunger, danger = super().evaluate_needs(a)
        if a.alive and a.stage != 'dependent' and action in ('search', 'explore'):
            reserve = self.book.energy[self.physical.reserve(a)]
            if reserve < LOW_RESERVE and not danger:
                action = 'rest'
                self.needs_last[a.id] = action
                self.conservation_metrics['conserved_actions'] += 1
        return action, hunger, danger

def enable_conservation(sim):
    enable_transition_support(sim)
    if type(sim.bridge) is not JuvenileTransitionBridge138:
        raise TypeError('expected Cycle138 bridge')
    sim.bridge.__class__ = ConservationBridge139
    sim.bridge.conservation_metrics = Counter()
    return sim
