"""Cycle092: directly edible Book-funded fifth habitat, opt-in only."""
from integrated_02191 import Unified291
from edible_capacity_02192 import EdibleCapacity
class Unified292(Unified291):
    def __init__(self,*args,edible_budget=0,**kwargs):
        super().__init__(*args,forage_budget=0,**kwargs)
        self.edible_policy=EdibleCapacity(edible_budget)
        self.edible_events=[]
    def step(self):
        super().step()
        if self.days%30==0:
            self.edible_events.append({'day':self.days,**self.edible_policy.act(self.bridge.tree)})
            self._check()
