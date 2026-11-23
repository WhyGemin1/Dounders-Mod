"""Cycle089 opt-in periodic donor-funded capacity; no scheduler changes."""
from integrated_02188 import Unified288
from capacity_renewal_02189 import renew_floodplain
class Unified289(Unified288):
    def __init__(self,*args,renewal_scale=0.,**kwargs):
        super().__init__(*args,**kwargs)
        if renewal_scale < 0 or renewal_scale > 1: raise ValueError('renewal_scale')
        self.renewal_scale=renewal_scale
        self.renewals=[]
    def step(self):
        super().step()
        if self.renewal_scale and self.days%30==0:
            self.renewals.append({'day':self.days,**renew_floodplain(self.bridge.tree,self.renewal_scale)})
            self._check()
