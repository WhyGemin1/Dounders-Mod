"""Cycle076: opt-in, read-only causal energy bottleneck classification."""
from collections import Counter
from energy_guard_02175 import EnergyGuardBridge275
class EnergyPathBridge276(EnergyGuardBridge275):
    def evaluate_needs(self,a):
        action,hunger,danger=super().evaluate_needs(a)
        if not getattr(self,'energy_path_audit',False) or a.species not in ('field_mouse','meadow_grazer','forest_browser') or a.stage=='dependent':
            return action,hunger,danger
        m=self.energy_path_metrics
        reserve=self.book.energy[self.physical.reserve(a)]
        if reserve>=.0005:return action,hunger,danger
        m['low_reserve_decisions']+=1
        m['action_'+action]+=1
        if danger:m['danger_deferrals']+=1
        plant=self.book.mass[self.physical.plant(a)]
        chem=self.book.energy[self.physical.chem(a)]
        if plant<=.04:m['plant_limited']+=1
        elif chem<=.00032:m['chemical_limited']+=1
        elif action=='feed':m['already_feeding']+=1
        else:m['action_priority_limited']+=1
        return action,hunger,danger
    def _feed_stock(self,a,source,kind):
        before=self.book.energy[self.physical.reserve(a)]
        result=super()._feed_stock(a,source,kind)
        if getattr(self,'energy_path_audit',False):
            m=self.energy_path_metrics
            m['feed_attempts']+=1
            m['feed_success' if result else 'feed_failure']+=1
            m['feed_gain_micro']+=round(max(0,self.book.energy[self.physical.reserve(a)]-before)*1e6)
        return result
