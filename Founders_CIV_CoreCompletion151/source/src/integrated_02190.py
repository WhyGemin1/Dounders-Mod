"""Cycle090 opt-in finite capacity policy, with canonical schedulers untouched."""
from integrated_02189 import Unified289
from capacity_policy_02190 import FiniteFloodplainPolicy
class Unified290(Unified289):
    def __init__(self,*args,policy_budget=0,policy_scale=.5,policy_trigger=.8,**kwargs):
        super().__init__(*args,renewal_scale=0,**kwargs)
        self.capacity_policy=FiniteFloodplainPolicy(policy_budget,policy_scale,policy_trigger)
        self.capacity_policy.reference=self.host.book.mass[self.bridge.tree.acct('plant','floodplain')]
        self.policy_events=[]
    def step(self):
        super().step()
        if self.days%30==0:
            self.policy_events.append({'day':self.days,**self.capacity_policy.act(self.bridge.tree)})
            self._check()
