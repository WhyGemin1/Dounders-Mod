"""Cycle075: opt-in deficit guard layered on the authoritative Cycle074 runtime."""
from collections import Counter
from integrated_02174 import Unified274
from energy_guard_02175 import EnergyGuardBridge275
class Unified275(Unified274):
    def __init__(self,*args,energy_guard=False,**kwargs):
        super().__init__(*args,**kwargs)
        self.bridge.__class__=EnergyGuardBridge275
        self.bridge.energy_guard=bool(energy_guard)
        self.bridge.energy_guard_metrics=Counter()
        self.energy_guard=bool(energy_guard)
        self._check()
    def report(self):
        r=super().report()
        r['energy_guard']={'enabled':self.energy_guard,**dict(self.bridge.energy_guard_metrics)}
        return r
