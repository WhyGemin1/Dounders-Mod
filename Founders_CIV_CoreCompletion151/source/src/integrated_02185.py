"""Optional Cycle085 candidate; preserves both demographic schedulers."""
from integrated_02184 import Unified284
from reproduction_02185 import ReproductiveBridge285

class Unified285(Unified284):
    def __init__(self, *args, compensatory_grazing=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.bridge.__class__ = ReproductiveBridge285
        self.bridge.compensatory_grazing = bool(compensatory_grazing)
        self.compensatory_grazing = bool(compensatory_grazing)
        self._check()
