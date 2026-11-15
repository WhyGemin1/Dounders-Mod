"""Cycle077 opt-in mortality trace; preserves parent demographic schedulers."""
from collections import Counter
from integrated_02176 import Unified276
from mortality_02177 import MortalityBridge277
class Unified277(Unified276):
    def __init__(self,*args,mortality_audit=False,**kwargs):
        super().__init__(*args,**kwargs)
        self.bridge.__class__=MortalityBridge277
        self.bridge.mortality_audit=bool(mortality_audit)
        self.bridge.mortality_metrics=Counter()
        self.mortality_audit=bool(mortality_audit)
        self._check()
    def report(self):
        r=super().report()
        r['mortality_audit']={'enabled':self.mortality_audit,**dict(self.bridge.mortality_metrics)}
        return r
