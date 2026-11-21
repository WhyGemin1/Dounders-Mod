"""Cycle078 opt-in replacement policy; no additional metrics or accounts."""
from knowledge_family_02142 import KnowledgeFamilyBridge242
from species_life_02115 import PROFILES, PREY

HERBIVORES=('field_mouse','meadow_grazer','forest_browser')
class UnifiedBehaviorBridge278(KnowledgeFamilyBridge242):
    def evaluate_needs(self,a):
        action,hunger,danger=super().evaluate_needs(a)
        if not getattr(self,'unified_behavior',False) or a.species not in HERBIVORES or a.stage=='dependent':
            return action,hunger,danger
        # Consolidate three experimental hunger/feeding guards into one policy.
        # Never override concealment in immediate danger or parental care.
        reserve=self.book.energy[self.physical.reserve(a)]
        demand=.001*(.5+.5*PROFILES[a.species].metabolism/.1)
        plant=self.book.mass[self.physical.plant(a)]
        chem=self.book.energy[self.physical.chem(a)]
        if not danger and action not in ('care','mate') and reserve<4*demand and plant>.04 and chem>.0004:
            return 'feed',hunger,danger
        return action,hunger,danger

    def _migrate(self,a,decision=None):
        if not getattr(self,'unified_behavior',False) or a.species not in HERBIVORES or a.stage=='dependent':
            return super()._migrate(a,decision)
        if decision in ('care','mate','rest','stay_with_caregiver'):
            return super()._migrate(a,decision)
        here=a.habitat
        local=self.book.mass[self.physical.plant(a)]
        # Compare food per consumer, not absolute stocks. Travel is finite.
        local_n=sum(x.alive and x.habitat==here and x.species in HERBIVORES for x in self.actors.values())
        local_share=local/max(1,local_n)
        options=[]
        for dest in self.tree.habitats[here].neighbors:
            n=sum(x.alive and x.habitat==dest and x.species in HERBIVORES for x in self.actors.values())
            share=self.book.mass[self.tree.acct('plant',dest)]/(n+1)
            if share>local_share*1.35 and share>local_share+.02:
                options.append((share,dest))
        if options and self.book.energy[self.physical.reserve(a)]>=self.TRAVEL_COST+.002:
            _,dest=max(options,key=lambda item:(item[0],item[1]))
            self.book.move(energy=[(self.physical.reserve(a),'environment:heat',self.TRAVEL_COST)])
            a.habitat=dest;a.hidden=False
            self._log('migration',actor=a.id,species=a.species,from_habitat=here,to_habitat=dest,
                      reason='unified_foraging',energy_cost=self.TRAVEL_COST)
            return True
        return super()._migrate(a,decision)
