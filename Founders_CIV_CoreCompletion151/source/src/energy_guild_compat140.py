"""Compatibility proof only: compose Cycle139 energy demand with Cycle138-G guilds.

E is a fourth opt-in factor. E=0 retains all legacy behavior. E=1 applies
Cycle139's uncalibrated rates but deliberately does NOT also enable the
Cycle136/138 juvenile-support switches. This is NOT an empirical model.
"""
from collections import Counter
from eco_factorial_cycle138 import EcoBridge138
from trophic_guilds_cycle138 import GuildBridge138, UnifiedTrophicGuild138
from energy_conservation_cycle139 import ConservationBridge139, LOW_RESERVE

class _EnergyCompatMixin:
    def _metabolize(self, a):
        # Cycle139 implementation uses only self.book, physical, needs_last,
        # conservation_metrics, and PROFILES; no mutation of the master Book.
        return ConservationBridge139._metabolize(self, a)

    def evaluate_needs(self, a):
        action, hunger, danger = super().evaluate_needs(a)
        if a.alive and a.stage != 'dependent' and action in ('search', 'explore'):
            reserve = self.book.energy[self.physical.reserve(a)]
            if reserve < LOW_RESERVE and not danger:
                action = 'rest'
                self.needs_last[a.id] = action
                self.conservation_metrics['conserved_actions'] += 1
        return action, hunger, danger

class EcoEnergyBridge140(_EnergyCompatMixin, EcoBridge138):
    pass

class GuildEnergyBridge140(_EnergyCompatMixin, GuildBridge138):
    pass

class UnifiedGuildEnergy140(UnifiedTrophicGuild138):
    def __init__(self, *, energy_conservation=False, **kwargs):
        if type(energy_conservation) is not bool:
            raise TypeError('energy_conservation must be bool')
        super().__init__(**kwargs)
        self.energy_conservation = energy_conservation
        if energy_conservation:
            expected = GuildBridge138 if self.expanded_food_web else EcoBridge138
            if type(self.bridge) is not expected:
                raise TypeError('unexpected bridge before energy combination')
            self.bridge.__class__ = (GuildEnergyBridge140 if self.expanded_food_web
                                     else EcoEnergyBridge140)
            self.bridge.conservation_metrics = Counter()
            assert self.host.book is self.bridge.book is self.bridge.tree.book
            self._check()
