"""Cycle090: opt-in finite, conditional floodplain support policy.

A founder maintenance decision is represented by an explicit finite budget, not
by minting biomass. The budget counts successful renewal actions; all physical
transfers still debit the existing authoritative donor accounts.
"""
from capacity_renewal_02189 import renew_floodplain

class FiniteFloodplainPolicy:
    def __init__(self, budget=3, scale=.5, trigger_fraction=.8):
        if not isinstance(budget,int) or budget<0: raise ValueError('budget')
        if not 0 < scale <= 1: raise ValueError('scale')
        if not 0 < trigger_fraction <= 1: raise ValueError('trigger_fraction')
        self.remaining=budget
        self.scale=scale
        self.trigger_fraction=trigger_fraction
        self.reference=None
    def act(self,tree):
        if tree.state!='active' or 'floodplain' not in tree.habitats:
            return {'funded':False,'reason':'inactive_or_missing'}
        book=tree.book
        target=tree.acct('plant','floodplain')
        current=book.mass[target]
        if self.reference is None:self.reference=current
        if self.remaining<=0:return {'funded':False,'reason':'budget_exhausted'}
        if current >= self.reference*self.trigger_fraction:
            return {'funded':False,'reason':'capacity_sufficient'}
        result=renew_floodplain(tree,self.scale)
        if result['funded']:self.remaining-=1
        return result
