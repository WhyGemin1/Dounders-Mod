from integrated_02180 import Unified280
from reproduction_02181 import ReproductiveBridge281
class Unified281(Unified280):
    def __init__(self,*args,juvenile_provisioning=False,**kwargs):
        super().__init__(*args,**kwargs)
        self.bridge.__class__=ReproductiveBridge281
        self.bridge.juvenile_provisioning=bool(juvenile_provisioning)
        self.juvenile_provisioning=bool(juvenile_provisioning)
        self._check()
