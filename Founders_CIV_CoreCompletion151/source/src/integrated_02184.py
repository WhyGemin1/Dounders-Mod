from integrated_02183 import Unified283
from reproduction_02184 import ReproductiveBridge284

class Unified284(Unified283):
    def __init__(self, *args, lactation_growth=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.bridge.__class__ = ReproductiveBridge284
        self.bridge.lactation_growth = bool(lactation_growth)
        self.lactation_growth = bool(lactation_growth)
        self._check()
