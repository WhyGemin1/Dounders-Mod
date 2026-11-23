"""Cycle070 opt-in ecological resource accessibility on integrated Cycle060 engine."""
from integrated_02160 import Unified260
from resource_access_02170 import ResourceAccessBridge270

class Unified270(Unified260):
    def __init__(self,*args,resource_access=True,**kwargs):
        super().__init__(*args,**kwargs)
        old=self.bridge
        # Preserve the already initialized actors, Book, RNG, family claims,
        # positions, and physical accounts. No second initialization or ledger.
        old.__class__=ResourceAccessBridge270
        old.resource_access=bool(resource_access)
        old.resource_access_metrics={'guided_moves':0,'unaffordable_moves':0,'evaluations':0,'depleted_opportunities':0,'no_gradient':0,'pressure_opportunities':0,'pressure_moves':0}
        self.resource_access=bool(resource_access)
        self._check()

    def report(self):
        r=super().report()
        r['resource_access']={'enabled':self.resource_access,
                              **self.bridge.resource_access_metrics}
        return r
