"""Cycle042: opt-in family effort routed through existing RSW-K cognition.

No additional knowledge engine, ledger or actor scheduler: claims are recorded
in `tree.sim.knowledge`, Cognition is attached to the existing LifeAnimal.
"""
from collections import Counter
from family_pair_02136 import (HabitatBridge239, PARTNER_RESERVE_FLOOR,
    PARENTAL_PROVISION_MASS, PARENTAL_WORK_COST)
from spatial_map_02137 import SpatialBridge240
from species_life_02115 import PROFILES, MASS_SCALE
from knowledge_architecture import Claim, Cognition, encounter

class KnowledgeFamilyBridge242(SpatialBridge240):
    def __init__(self, tree, seed=9711, counts=None, *, resource_aware_family=False,
                 **kwargs):
        self.resource_aware_family=bool(resource_aware_family)
        self.family_knowledge_metrics=Counter()
        super().__init__(tree,seed,counts,**kwargs)

    @staticmethod
    def cognition(actor):
        if not hasattr(actor,'cognition'):
            actor.cognition=Cognition()
        return actor.cognition

    def _claim_id(self, mother):
        return f'family_food_method:{self.tree.id}:{mother.species}:{mother.habitat}'

    def _provision_mother(self, mother, father):
        if not self.resource_aware_family:
            return super()._provision_mother(mother,father)
        world=self.tree.sim.knowledge
        claim_id=self._claim_id(mother)
        if claim_id not in world.claims:
            world.add(Claim(claim_id, f'family_local_food:{mother.species}:{mother.habitat}',
                'A local resource and caregiver reserve assessment can inform reproduction.',
                kind='procedure'))
        cogn=self.cognition(father)
        relation=cogn.claim(claim_id)
        # Only co-located family members observe/communicate resource status.
        # Repeated observation improves the EXISTING RSW-K knowledge relation.
        encounter(world,cogn,self.day,father.id,claim_id,
                  source=f'local_habitat:{mother.habitat}',medium='observation',
                  fidelity=.75,trust=.60)
        self.family_knowledge_metrics['local_food_observations']+=1
        if not mother.alive or not father.alive or self.partner(mother) is not father:
            self.family_knowledge_metrics['declined_pair_unavailable']+=1
            return False
        p=PROFILES[mother.species]
        required=p.birth_cost*MASS_SCALE
        shortage=max(0.,required-self.book.mass[self.physical.maternal(mother)])
        if shortage<=1e-10:
            return False
        carrion=self.carrion(mother.habitat)
        use_carrion=(mother.species=='ridge_hound' or
                     (mother.species=='carrion_bird' and self.book.mass[carrion]>=.0004))
        source=(carrion if use_carrion else self.tree.acct('plant',mother.habitat))
        stock=self.book.mass[source]
        # The uncertainty buffer narrows with accumulated knowledge; it never
        # allows an unfunded transfer or bypass of the base biological rules.
        food_buffer=(.001 if use_carrion else .04)+(.003 if use_carrion else .025)*(1-relation.understanding)
        net_food=max(0.,stock-food_buffer)
        donor=self.physical.reserve(father)
        reserve=self.book.energy[donor]
        # Preserve enough energy for expected near-term self-maintenance.
        daily_demand=.001*(.5+.5*p.metabolism/.1)
        # Safeguard maintenance before investing: a less understood habitat
        # requires a longer uncertainty buffer, which verified observation and
        # successful practice gradually shrink. Dependent care is also a real
        # opportunity cost on this father's current metabolic reserve.
        existing_dependents=sum(x.alive and x.stage=='dependent' and
              father.id in x.caregiver_ids and x.habitat==father.habitat
              for x in self.actors.values())
        horizon_days=8.+8.*(1.-relation.understanding)
        safety_floor=PARTNER_RESERVE_FLOOR+daily_demand*horizon_days+existing_dependents*.0006
        feasible=(net_food>=min(.0004,shortage) and
                  reserve>=safety_floor+PARENTAL_WORK_COST and
                  mother.condition>=.55 and father.condition>=.55)
        if not feasible:
            self.family_knowledge_metrics['investment_declined_resource_or_health']+=1
            world.record(self.day,father.id,'family_investment_declined',claim_id,
                         local_mass=round(stock,8),usable_mass=round(net_food,8),
                         own_reserve=round(reserve,8),
                         maintenance_buffer=round(safety_floor,8))
            return False
        old_energy=self.book.energy[donor]
        done=super()._provision_mother(mother,father)
        if done:
            self.family_knowledge_metrics['funded_investments']+=1
            # Practice refers to a materially verified outcome, not a guessed
            # claim of success; the world ledger remains source of truth.
            relation.practiced+=1
            relation.understanding=min(1.,relation.understanding+.025)
            relation.confidence=min(1.,relation.confidence+.012)
            mom_cogn=self.cognition(mother)
            encounter(world,mom_cogn,self.day,mother.id,claim_id,
                      source=father.id,medium='spoken',fidelity=.65,trust=.7)
            mom_cogn.partner(father.id).update('benevolence',True,strength=.2)
            world.record(self.day,father.id,'family_investment_funded',claim_id,
                         energy_cost=round(old_energy-self.book.energy[donor],8))
        else:
            self.family_knowledge_metrics['investment_declined_book_or_base_gates']+=1
        return done

    def census(self):
        out=super().census()
        out['knowledge_family_enabled']=self.resource_aware_family
        out['knowledge_family_metrics']=dict(self.family_knowledge_metrics)
        out['family_knowledge_practice']=sum(
            getattr(a,'cognition',None) is not None and
            sum(k.practiced for k in a.cognition.knowledge.values()) or 0
            for a in self.actors.values())
        return out
