from integrated_02182 import Unified282
from reproduction_02183 import ReproductiveBridge283
class Unified283(Unified282):
    def __init__(self,*args,natal_foraging=False,**kwargs):
        super().__init__(*args,**kwargs)
        self.bridge.__class__=ReproductiveBridge283
        self.bridge.natal_foraging=bool(natal_foraging)
        self.natal_foraging=bool(natal_foraging)
        self._check()
