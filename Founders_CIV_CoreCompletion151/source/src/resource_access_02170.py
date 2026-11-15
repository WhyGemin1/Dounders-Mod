"""Opt-in neighbor-aware herbivore foraging; finite travel debit, no new accounts."""
from knowledge_family_02142 import KnowledgeFamilyBridge242

class ResourceAccessBridge270(KnowledgeFamilyBridge242):
    """Replace random hunger migration with local resource-gradient movement.

    Uses only current and adjacent habitat plant Book balances. The actual
    feed/migration scheduler and all physical transfers remain unchanged.
    """
    def __init__(self,*args,resource_access=True,**kwargs):
        self.resource_access=bool(resource_access)
        self.resource_access_metrics={'guided_moves':0,'unaffordable_moves':0,'evaluations':0,'depleted_opportunities':0,'no_gradient':0,'pressure_opportunities':0,'pressure_moves':0}
        super().__init__(*args,**kwargs)

    def _migrate(self,a,decision=None):
        if not self.resource_access or a.species in ('ridge_hound','carrion_bird'):
            return super()._migrate(a,decision)
        if a.stage=='dependent' or decision not in ('feed','explore','search'):
            return super()._migrate(a,decision)
        here=a.habitat
        source=self.physical.plant(a)
        current=self.book.mass[source]
        # Only adjacent accessible habitat balances; no global map knowledge.
        self.resource_access_metrics['evaluations']+=1
        if current < .22: self.resource_access_metrics['depleted_opportunities']+=1
        choices=[]
        for dest in self.tree.habitats[here].neighbors:
            stock=self.book.mass[self.tree.acct('plant',dest)]
            if stock>current+0.04 and stock>0.04:
                choices.append((stock,dest))
        if not choices:
            self.resource_access_metrics['no_gradient']+=1
            return super()._migrate(a,decision)
        # Food is shared with co-located herbivores.  Assess available food
        # per competing consumer rather than relying on a fixed stock floor.
        herbivores=('field_mouse','meadow_grazer','forest_browser')
        competitors=sum(x.alive and x.species in herbivores and
                        x.habitat==here for x in self.actors.values())
        local_share=current/max(1,competitors)
        ranked=[]
        for _,dest in choices:
            neighbor_count=sum(x.alive and x.species in herbivores and
                               x.habitat==dest for x in self.actors.values())
            neighbor_share=self.book.mass[self.tree.acct('plant',dest)]/(neighbor_count+1)
            ranked.append((neighbor_share,dest))
        # A conservative, opt-in pilot: move only when expected share is at
        # least 1.5x local share and food pressure is meaningful (<0.12/animal).
        if not ranked or local_share>=.12:
            return super()._migrate(a,decision)
        best_share,dest=max(ranked,key=lambda item:(item[0],item[1]))
        if best_share<=max(local_share*1.5,local_share+.015):
            return super()._migrate(a,decision)
        self.resource_access_metrics['pressure_opportunities']+=1
        reserve=self.physical.reserve(a)
        if self.book.energy[reserve]<self.TRAVEL_COST+.001:
            self.resource_access_metrics['unaffordable_moves']+=1
            return super()._migrate(a,decision)
        self.book.move(energy=[(reserve,'environment:heat',self.TRAVEL_COST)])
        a.habitat=dest;a.hidden=False
        self._log('migration',actor=a.id,species=a.species,from_habitat=here,
                  to_habitat=dest,reason='adjacent_resource_gradient',energy_cost=self.TRAVEL_COST)
        self.resource_access_metrics['guided_moves']+=1
        self.resource_access_metrics['pressure_moves']+=1
        return True
