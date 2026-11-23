"""Cycle093: explicitly scheduled finite floodplain capacity funding experiment.
No canonical or demographic scheduler changes.
"""
from integrated_02192 import Unified292

class Unified293(Unified292):
    def __init__(self,*args,scheduled_funding=False,**kwargs):
        super().__init__(*args,**kwargs)
        self.scheduled_funding=bool(scheduled_funding)
    def step(self):
        # EdibleCapacity's existing Book transaction and donor guards remain authoritative.
        # In scheduled arm, bypass only the forage threshold, never the finite budget.
        if self.scheduled_funding and (self.days+1)%30==0:
            self.edible_policy.reference=float('inf')
        super().step()
