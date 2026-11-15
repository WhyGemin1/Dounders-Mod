"""Opt-in forage allocation; no changes to either demographic scheduler."""
from integrated_02190 import Unified290
from forage_funding_02191 import ForageFunding
class Unified291(Unified290):
    def __init__(self,*args,forage_budget=0,forage_plant=.5,forage_energy=.1,**kwargs):
        super().__init__(*args,policy_budget=0,**kwargs)
        self.forage_policy=ForageFunding(forage_budget,forage_plant,forage_energy)
        self.forage_policy.reference=self.host.book.mass[self.bridge.tree.acct('plant','floodplain')]
        self.forage_events=[]
    def step(self):
        super().step()
        if self.days%30==0:
            self.forage_events.append({'day':self.days,**self.forage_policy.act(self.bridge.tree)})
            self._check()
