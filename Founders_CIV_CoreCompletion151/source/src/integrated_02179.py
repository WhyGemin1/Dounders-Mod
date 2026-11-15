"""Cycle079 experimental, opt-in metabolic conservation; no canonical change."""
from integrated_02178 import Unified278
from energy_budget_02179 import EnergyBudgetBridge279
class Unified279(Unified278):
    def __init__(self,*args,energy_budget=False,**kwargs):
        super().__init__(*args,**kwargs)
        self.bridge.__class__=EnergyBudgetBridge279
        self.bridge.energy_budget=bool(energy_budget)
        self.energy_budget=bool(energy_budget)
        self._check()
