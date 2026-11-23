"""Cycle074 opt-in adaptive feeding layered on Cycle073; one Book/clock."""
from collections import Counter
from integrated_02170 import Unified270
from adaptive_feeding_02174 import AdaptiveFeedingBridge274

class Unified274(Unified270):
    def __init__(self,*args,adaptive_feeding=False,**kwargs):
        super().__init__(*args,**kwargs)
        self.bridge.__class__ = AdaptiveFeedingBridge274
        self.bridge.adaptive_feeding = bool(adaptive_feeding)
        self.bridge.feeding_metrics = Counter()
        self.adaptive_feeding = bool(adaptive_feeding)
        self._check()

    def report(self):
        r = super().report()
        r['adaptive_feeding'] = {'enabled':self.adaptive_feeding,**dict(self.bridge.feeding_metrics)}
        return r
