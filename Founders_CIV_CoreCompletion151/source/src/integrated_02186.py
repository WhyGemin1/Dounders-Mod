"""Cycle086 opt-in maturation-feeding branch; canonical untouched."""
from integrated_02185 import Unified285
from reproduction_02186 import ReproductiveBridge286
class Unified286(Unified285):
    def __init__(self,*args,maturation_feeding=False,**kwargs):
        super().__init__(*args,**kwargs)
        self.bridge.__class__=ReproductiveBridge286
        self.bridge.maturation_feeding=bool(maturation_feeding)
        self.maturation_feeding=bool(maturation_feeding)
        self._check()
