"""Opt-in, observation-only mortality/energy accounting; no Book writes."""
from collections import Counter
from energy_path_02176 import EnergyPathBridge276

class MortalityBridge277(EnergyPathBridge276):
    def _feed_stock(self,a,source,kind):
        before=self.book.energy[self.physical.reserve(a)]
        result=super()._feed_stock(a,source,kind)
        if getattr(self,'mortality_audit',False):
            m=self.mortality_metrics
            m['feeding_attempts']+=1
            if result:m['feeding_successes']+=1
            m['energy_gained_micro']+=round(max(0.,self.book.energy[self.physical.reserve(a)]-before)*1e6)
        return result

    def _death(self,a,cause):
        if getattr(self,'mortality_audit',False) and a.alive:
            m=self.mortality_metrics
            # Record state before the parent death method can redistribute resources.
            m['death_attempt_'+str(cause)]+=1
            m['death_attempt_species_'+str(a.species)]+=1
            reserve=self.book.energy[self.physical.reserve(a)]
            m['death_attempt_reserve_micro']+=round(reserve*1e6)
            m['death_attempt_condition_milli']+=round(a.condition*1000)
            was_alive=a.alive
            result=super()._death(a,cause)
            if was_alive and not a.alive:
                m['confirmed_deaths']+=1
                m['confirmed_'+str(cause)]+=1
            else:m['deferred_deaths']+=1
            return result
        return super()._death(a,cause)
