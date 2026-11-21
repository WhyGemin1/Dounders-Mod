"""Cycle145: resource-limited life-history corrections on the one Core144 Book.

No added energy, artificial births, or immortality. Fixes the known gap between
chronological maturity and somatic growth, adjusts the mismatched fixed maternal
and fuel gates, and drives food seeking from development as well as circulating
fuel. Optional perturbations exist ONLY for matched causal tests.
"""
from __future__ import annotations
from collections import Counter
from math import isfinite
from random import Random

from core_completion_144 import (UnifiedCoreCompletion144, CoreCompletionBridge144, CoreCompletionWorld144,
    fraction_over_elapsed, SHARED_ABSORPTION_RATE)
from species_life_02115 import PROFILES, MASS_SCALE, YEAR
from core_physiology_v2 import PREY, ANTS, MEGA
from five_phase_core_142 import ANIMAL_TISSUE_ENERGY_DENSITY
from trophic_guilds_cycle138 import ALLOWED_HABITATS
from founders_civ.experimental.social_agents import stable_seed

class CoreCompletionBridge145(CoreCompletionBridge144):
    """One active animal physiology; override resource allocation and eligibility."""
    def activate_life_cycle_repair(self, *, maintenance_factor=1.0, predation=True):
        if not (.25 <= maintenance_factor <= 2.0):
            raise ValueError('research perturbation maintenance_factor must be .25..2')
        self.maintenance_factor=float(maintenance_factor)
        self.predation_enabled=bool(predation)
        self.life_metrics=Counter()
        self.life_blockers=Counter()

    def _maintenance_demand(self,a):
        return super()._maintenance_demand(a)*self.maintenance_factor

    def _digest(self, a, dt=1.):
        """Persist actual growth beyond chronological maturity until body develops.

        Existing Book accounts are the only source of structural, maternal and
        stored energy. Assimilation byproducts are routed to heat and detritus.
        This corrects the previous bug where growth stopped the day maturity
        age was reached, even if bodies were <30% adult size.
        """
        b=self.book;ph=self.physical;s=self._state(a)
        gut=ph.gut(a);gm=b.mass[gut]
        if gm<=1e-12:return
        q=gm*fraction_over_elapsed(SHARED_ABSORPTION_RATE*self._trait(a).digestion,dt)
        ge=self._gut_energy(a);e=b.energy[ge]*q/max(gm,1e-12)
        p=PROFILES[a.species];adult_target=p.adult_mass()
        current_mass=b.mass[ph.live(a)]
        mass_gap=max(0.,adult_target-current_mass)
        # Investment in tissue is developmental, not an age-limited switch.
        juvenile=a.age<p.maturity
        structural_fraction=.62 if juvenile else .45
        grow=min(mass_gap,q*structural_fraction)
        # Reproductive tissue is only built from diet after sufficient somatic growth.
        maternal=0.
        if a.sex=='F' and a.age>=p.maturity and current_mass>=adult_target*.75:
            maternal=min(q*.43, max(0.,p.maternal_cap()-b.mass[ph.maternal(a)]),q-grow)
        waste=max(0.,q-grow-maternal)
        legs=[(gut,dst,val) for dst,val in ((ph.live(a),grow),
              (ph.maternal(a),maternal),(ph.detritus(a),waste)) if val>1e-12]
        if legs:ph.convert(legs)
        quality=max(0.,min(1.,s.gut_quality_weight/max(s.gut_energy_weight,1e-12)))
        if e>1e-12:
            useful=e*quality
            tissue=useful*grow/max(q,1e-12)
            reproduction=useful*maternal/max(q,1e-12)
            available=max(0.,useful-tissue-reproduction)
            short=self._short(a);reserve=ph.reserve(a)
            short_goal=max(.0005,self._maintenance_demand(a)*2.0)
            long_goal=max(.0015,self._maintenance_demand(a)*25.,adult_target*.035)
            to_short=min(available,max(0.,short_goal-b.energy[short]))
            to_reserve=min(max(0.,available-to_short),max(0.,long_goal-b.energy[reserve]))
            to_short+=available-to_short-to_reserve
            energy=[(ge,dest,val) for dest,val in ((ph.tissue(a),tissue),
              (ph.maternal_energy(a),reproduction),(short,to_short),
              (reserve,to_reserve),('environment:heat',e-useful)) if val>1e-12]
            if energy:b.move(energy=energy)
            self.physiology_metrics['absorbed_energy']+=useful
            self.physiology_metrics['digestion_heat']+=e-useful
            self.life_metrics['reserve_from_diet']+=to_reserve
            self.life_metrics['reproductive_energy_from_diet']+=reproduction
            s.gut_energy_weight=max(0.,s.gut_energy_weight-e)
            s.gut_quality_weight=max(0.,s.gut_quality_weight-e*quality)
        self.physiology_metrics['digested_mass']+=q
        self.life_metrics['somatic_growth_from_diet']+=grow
        self.life_metrics['maternal_growth_from_diet']+=maternal

    def _choose(self,a):
        action,hunger,danger=super()._choose(a)
        if a.stage=='dependent' or action in ('flee','hide','sleep') or danger:
            return action,hunger,danger
        if a.species in PREY or a.species=='carrion_bird':
            return action,hunger,danger
        if a.species==ANTS:return action,hunger,danger
        s=self._state(a)
        if s.fatigue>=.64 or s.readiness<=.32:return action,hunger,danger
        p=PROFILES[a.species]
        body=self.book.mass[self.physical.live(a)]
        target=p.adult_mass()
        developmental=body<target*.95
        maternal=(a.sex=='F' and a.age>=p.maturity and body>=target*.75 and
                  self.book.mass[self.physical.maternal(a)]<self._minimum_maternal_mass(p))
        gut=self.book.mass[self.physical.gut(a)]
        # Don't force another meal when food is already being processed.
        if (developmental or maternal) and gut<max(.001,target*.16):
            self.life_metrics['developmental_foraging_decisions']+=1
            return 'feed',max(hunger,.65),danger
        return action,hunger,danger

    @staticmethod
    def _minimum_maternal_mass(p):
        # The original birth_cost parameter is NOT a single newborn's mass.
        # Insist on a material foundation for the minimum natural litter while
        # avoiding the previous overlarge generic maternal gate.
        return max(p.newborn_mass()*p.litter[0],p.birth_cost*MASS_SCALE*.53)

    def _hunt(self,a):
        if not self.predation_enabled:
            self.life_metrics['predation_test_suppressed']+=1
            return False
        return super()._hunt(a)

    def _reproduce(self):
        """Conception only after actual physique, reproductive stock, fuel and mate.

        The old hard-coded 0.012 reserve threshold exceeded healthy small
        mammals' physically achievable reserves. Thresholds scale to actual
        upkeep and offspring funding. No free births or guaranteed conceptions.
        """
        phase=self.day%YEAR
        for mom in list(self.actors.values()):
            if not mom.alive or mom.sex!='F':continue
            p=PROFILES[mom.species]
            if mom.pregnant_until is not None:
                if self.day>=mom.pregnant_until:self._birth(mom)
                continue
            if mom.stage!='adult' or not(p.breeding[0]<=phase<=p.breeding[1]):
                self.life_blockers['not_adult_or_season']+=1;continue
            if mom.condition<.62 or self.book.mass[self.physical.live(mom)]<p.adult_mass()*.80:
                self.life_blockers['insufficient_body_or_condition']+=1;continue
            if self.day-mom.last_birth_day<p.gestation+p.independence:
                self.life_blockers['postpartum_recovery']+=1;continue
            minimum=self._minimum_maternal_mass(p)
            if self.book.mass[self.physical.maternal(mom)]+1e-12<minimum:
                self.life_blockers['maternal_mass']+=1;continue
            # Physical maternal tissue and fetus must be energetically funded.
            minimum_embodied=p.newborn_mass()*p.litter[0]*ANIMAL_TISSUE_ENERGY_DENSITY*.45
            if self.book.energy[self.physical.maternal_energy(mom)]+1e-12<minimum_embodied:
                self.life_blockers['maternal_embodied_energy']+=1;continue
            reserve=self.book.energy[self.physical.reserve(mom)]
            short=self.book.energy[self._short(mom)]
            needed=max(.0005,self._maintenance_demand(mom)*2.0)
            if reserve+short*.5<needed:
                self.life_blockers['mobilizable_energy']+=1;continue
            mates=[a for a in self.actors.values() if a.alive and a.id!=mom.id
                   and a.species==mom.species and a.sex=='M' and a.stage=='adult'
                   and a.habitat==mom.habitat and a.condition>=.60
                   and self.book.mass[self.physical.live(a)]>=p.adult_mass()*.70]
            if not mates:self.life_blockers['mate_absent']+=1;continue
            self.life_metrics['eligible_mating_days']+=1
            if self.rng.random()>=min(1.,.042*self._trait(mom).reproductive):continue
            father=self.rng.choice(mates)
            mom.pregnancy_father=father.id;mom.pregnant_until=self.day+p.gestation
            self._log('conception',mother=mom.id,father=father.id,due=mom.pregnant_until,
                      species=mom.species,maternal_stock=self.book.mass[self.physical.maternal(mom)])
            self.life_metrics['conceptions']+=1

    def _birth(self,mom):
        born=super()._birth(mom)
        if born:
            self.life_metrics['funded_births']+=born
            self.life_metrics[f'births_generation_{mom.generation+1}']+=born
        return born

class CoreCompletionWorld145(CoreCompletionWorld144):
    """Native digestion no longer hoards unlimited food mass inside residents.

    The previous fee-free gut intake continued for life even after body fuel
    already held ten times the original 0.34 food-mass buffer. This consumed
    plant biomass faster than production, blocked native recruitment, and led
    to old-age extinction despite abundant sunlight, soil and water.
    """
    NATIVE_RESERVE_TARGET=.34

    def _feed(self,r):
        inventory=self._five_phase_inventory
        lot=inventory.plant(r.habitat)
        inventory.balance(r.habitat)
        b=self.book
        gut=self._native_gut(r)
        stored=b.mass[f'fuel:{r.id}']+b.mass[gut]
        q=min(.06,max(0.,self.NATIVE_RESERVE_TARGET-stored),
              max(0.,.16-b.mass[gut]),inventory.available_mass(lot))
        if q<=.001:return False
        e=q*lot.nominal_density
        txn=b.ingest(material=[(lot.mass_account,gut,q)],
                     energy=[(lot.energy_account,self._native_gut_energy(r),e)])
        self.last_txn=txn
        self.counters['tree_grazing']+=1
        self.counters['native_gut_meals']+=1
        self.counters['native_homeostatic_meals']+=1
        self._event('tree_native_ingest',actor=r.id,habitat=r.habitat,
                    mass=q,energy=e,absorbed_immediately=0.,txn=txn)
        return True

class UnifiedCoreCompletion145(UnifiedCoreCompletion144):
    """Single authoritative Core144 engine, with life-history repairs in place."""
    def __init__(self,*args,maintenance_factor=1.,predation=True,**kwargs):
        super().__init__(*args,**kwargs)
        if type(self.bridge) is not CoreCompletionBridge144:
            raise TypeError('unexpected engine source for 145 repair')
        self.bridge.__class__=CoreCompletionBridge145
        self.bridge.activate_life_cycle_repair(maintenance_factor=maintenance_factor,
                                               predation=predation)
        if type(self.bridge.tree) is not CoreCompletionWorld144:
            raise TypeError("unexpected native World source for 145 repair")
        self.bridge.tree.__class__=CoreCompletionWorld145
        assert self.host.book is self.bridge.book is self.bridge.tree.book
        self.host.book.audit()

    def report(self):
        output=super().report()
        output['core_completion_145']={
            'status':'experimental_not_canonical',
            'maintenance_factor':self.bridge.maintenance_factor,
            'predation':self.bridge.predation_enabled,
            'reproductive_metrics':dict(self.bridge.life_metrics),
            'reproductive_blockers':dict(self.bridge.life_blockers),
            'one_book':self.host.book is self.bridge.book is self.bridge.tree.book}
        return output
