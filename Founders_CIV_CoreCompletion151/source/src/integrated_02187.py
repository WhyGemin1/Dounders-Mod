"""Cycle087 opt-in growth allocation branch; canonical untouched."""
from integrated_02186 import Unified286
from reproduction_02187 import ReproductiveBridge287
class Unified287(Unified286):
    def __init__(self,*args,growth_allocation=False,**kwargs):
        super().__init__(*args,**kwargs)
        self.bridge.__class__=ReproductiveBridge287
        self.bridge.growth_allocation=bool(growth_allocation)
        self.growth_allocation=bool(growth_allocation)
        self._check()
