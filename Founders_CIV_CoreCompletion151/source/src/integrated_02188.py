"""Cycle088 isolated opt-in dependent nutrition branch."""
from integrated_02187 import Unified287
from reproduction_02188 import ReproductiveBridge288
class Unified288(Unified287):
    def __init__(self,*args,dependent_nutrition=False,**kwargs):
        super().__init__(*args,**kwargs)
        self.bridge.__class__=ReproductiveBridge288
        self.bridge.dependent_nutrition=bool(dependent_nutrition)
        self.dependent_nutrition=bool(dependent_nutrition)
        self._check()
