"""Cycle076 energy-path diagnosis; canonical unchanged."""
from collections import Counter
from integrated_02175 import Unified275
from energy_path_02176 import EnergyPathBridge276
class Unified276(Unified275):
    def __init__(self,*args,energy_path_audit=False,**kwargs):
        super().__init__(*args,**kwargs)
        self.bridge.__class__=EnergyPathBridge276
        self.bridge.energy_path_audit=bool(energy_path_audit)
        self.bridge.energy_path_metrics=Counter()
        self.energy_path_audit=bool(energy_path_audit)
        self._check()
    def report(self):
        r=super().report()
        r['energy_path']={'enabled':self.energy_path_audit,**dict(self.bridge.energy_path_metrics)}
        return r
