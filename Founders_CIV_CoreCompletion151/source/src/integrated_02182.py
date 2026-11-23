from integrated_02181 import Unified281
from reproduction_02182 import ReproductiveBridge282
class Unified282(Unified281):
    def __init__(self,*args,juvenile_foraging=False,**kwargs):
        super().__init__(*args,**kwargs)
        self.bridge.__class__=ReproductiveBridge282
        self.bridge.juvenile_foraging=bool(juvenile_foraging)
        self.juvenile_foraging=bool(juvenile_foraging)
        self._check()
