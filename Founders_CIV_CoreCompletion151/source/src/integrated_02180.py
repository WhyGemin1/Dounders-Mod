from integrated_02179 import Unified279
from reproduction_02180 import ReproductiveBridge280
class Unified280(Unified279):
    def __init__(self,*args,reproductive_ecology=False,**kwargs):
        super().__init__(*args,**kwargs)
        self.bridge.__class__=ReproductiveBridge280
        self.bridge.reproductive_ecology=bool(reproductive_ecology)
        self.reproductive_ecology=bool(reproductive_ecology)
        self._check()
