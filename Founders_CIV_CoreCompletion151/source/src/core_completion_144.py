"""Cycle144: one-book completion pass over the executable Cycle143 engine.

Phase 1: preserve single physical Book + native/bridge schedulers.
Phase 2: heritable, bounded individual traits affect actual rate processes.
Phase 3: native migration consults paired edible lots, not obsolete chem proxy.
Phase 4: optional, finite Founder stewardship funds Creation upkeep separately
         from World producer energy.
Phase 5: test replay, conservation and life-cycle checkpoints (no automatic
         canonical promotion or hard-coded persistence).

All coefficients remain exploratory historical units, NOT calibrated SI physiology.
"""
from __future__ import annotations
from collections import Counter
from math import exp
from random import Random
from core_completion_143 import (UnifiedCoreCompletion143, CoreCompletionBridge143,
    CoreCompletionWorld143, EdibleInventory143, NATIVE_ASSIMILATION_FRACTION,
    NATIVE_GUT_MASS_CAP)
from five_phase_core_142 import ANIMAL_TISSUE_ENERGY_DENSITY
from species_traits_143 import (Phenotype143, founder_phenotype, descendant_phenotype,
    BLUEPRINTS)
from core_physiology_v2 import (PROFILES, PREY, COVER, ANTS, MEGA, YEAR)
from species_life_02115 import MASS_SCALE
from founder_world_energy_141 import WorldEnergyFunding141
from founders_civ.experimental.social_agents import stable_seed

# Numerical integration frequencies in world-days^-1; not actions per day.
SHARED_ABSORPTION_RATE = .72


def fraction_over_elapsed(rate, days):
    """Exact first-order rate integration; duration is measured, not spent."""
    if rate < 0 or days < 0:
        raise ValueError('negative physical rate or duration')
    return 1. - exp(-rate * days)


class EcologicalProduction144(EdibleInventory143):
    """Solar-energy assimilation into *existing* producer tissue.

    Photosynthesis is constrained by standing vegetation, soil and water and
    only occurs once per World age. It transfers finite solar Book energy,
    recording inefficiency as heat, never creating energy, mass or food tokens.
    """
    CONVERSION_EFFICIENCY=.58  # synthetic, pending empirical calibration
    CAPTURE_PER_MASS_DAY=.031

    def __init__(self,bridge):
        super().__init__(bridge)
        self._last_photo_age={}

    def balance(self,habitat):
        # First reconcile historic producer chemical energy without minting.
        super().balance(habitat)
        tree=self.bridge.tree
        if tree.state not in ('active','germinating'):
            return
        if self._last_photo_age.get(habitat)==tree.age:return
        self._last_photo_age[habitat]=tree.age
        b=self.bridge.book
        lot=self.plant(habitat)
        mass=b.mass[lot.mass_account]
        current=b.energy[lot.energy_account]
        deficit=max(0.,mass*lot.nominal_density-current)
        if mass<=1e-12 or deficit<=1e-12:return
        water=b.mass[tree.acct('water',habitat)]
        soil=b.mass[tree.acct('soil',habitat)]
        # Reduced capture under drought/nutrient shortage; no self-repair bonus.
        water_factor=min(1.,water/2.0)
        soil_factor=min(1.,soil/1.0)
        sun=tree.acct('sun',habitat)
        available=max(0.,b.energy[sun])
        captured=min(deficit,mass*self.CAPTURE_PER_MASS_DAY*water_factor*soil_factor,
                     available*self.CONVERSION_EFFICIENCY)
        if captured<=1e-12:return
        spent=captured/self.CONVERSION_EFFICIENCY
        txn=b.move(energy=[(sun,lot.energy_account,captured),
                           (sun,tree.acct('heat',habitat),spent-captured)])
        self.metrics['photosynthetic_capture_energy']+=captured
        self.metrics['photosynthetic_input_energy']+=spent
        self.metrics['photosynthetic_heat_energy']+=spent-captured
        self.metrics['photosynthetic_days']+=1


class CoreCompletionBridge144(CoreCompletionBridge143):
    """Active trait-informed physiology on the same Book as native residents."""
    def activate_traits(self):
        self.phenotypes = {}
        self.trait_metrics = Counter()
        for a in sorted(self.actors.values(), key=lambda x:x.id):
            if a.species not in BLUEPRINTS:
                raise ValueError('missing species blueprint: ' + a.species)
            rng = Random(stable_seed(self.seed, a.id, 'phenotype-144'))
            self.phenotypes[a.id] = founder_phenotype(a.species, rng)
        self.trait_metrics['founders_seeded'] = len(self.phenotypes)

    def _trait(self, a):
        """Late actors must be explicit newborns, not silently generic adults."""
        if a.id not in self.phenotypes:
            raise AssertionError('missing individual phenotype for ' + a.id)
        return self.phenotypes[a.id]

    def _maintenance_demand(self, a):
        return super()._maintenance_demand(a) * self._trait(a).basal

    def _digest(self, a, dt=1.):
        """Use one conserved gut conversion and trait-sensitive absorption rate."""
        b=self.book; ph=self.physical; s=self._state(a)
        gut=ph.gut(a); gm=b.mass[gut]
        if gm<=1e-12:return
        q=gm*fraction_over_elapsed(SHARED_ABSORPTION_RATE*self._trait(a).digestion, dt)
        ge=self._gut_energy(a)
        e=b.energy[ge]*q/max(gm,1e-12)
        p=PROFILES[a.species]
        target=p.adult_mass()*(.35+.65*min(1.,a.age/max(1,p.maturity)))
        grow=min(q*.12,max(0.,target-b.mass[ph.live(a)])) if a.age<p.maturity else 0.
        maternal=(min(q*.11,max(0.,p.maternal_cap()-b.mass[ph.maternal(a)]))
                  if a.sex=='F' and a.stage=='adult' else 0.)
        waste=max(0.,q-grow-maternal)
        material=[(gut,dst,n) for dst,n in ((ph.live(a),grow),
                 (ph.maternal(a),maternal),(ph.detritus(a),waste)) if n>1e-12]
        if material:ph.convert(material)
        quality=max(0.,min(1.,s.gut_quality_weight/max(s.gut_energy_weight,1e-12)))
        if e>1e-12:
            useful=e*quality
            tissue=useful*grow/max(q,1e-12)
            to_maternal=useful*maternal/max(q,1e-12)
            available=useful-tissue-to_maternal
            # A living animal should replenish long-term reserves when its
            # short-term mobilizable substrate is adequately supplied. This is
            # a *Book transfer* of actually absorbed food, never free storage.
            short_account=self._short(a)
            reserve_account=ph.reserve(a)
            short_goal=max(.0010, self._maintenance_demand(a)*2.0)
            reserve_goal=max(.012, self._maintenance_demand(a)*45.0,
                             self._bodymass(a)*.055)
            to_short=min(available,max(0.,short_goal-b.energy[short_account]))
            to_store=min(max(0.,available-to_short),
                         max(0.,reserve_goal-b.energy[reserve_account]))
            # Any nutrition not storable in reserve remains circulating.
            to_short+=available-to_short-to_store
            legs=[(ge,dst,n) for dst,n in ((ph.tissue(a),tissue),
                   (ph.maternal_energy(a),to_maternal),
                   (short_account,to_short),
                   (reserve_account,to_store),
                   ('environment:heat',e-useful)) if n>1e-12]
            if to_store>1e-12:
                self.trait_metrics['nutrition_stored_to_reserve']+=to_store
                self.trait_metrics['reserve_refill_events']+=1
            if legs:b.move(energy=legs)
            self.physiology_metrics['absorbed_energy']+=useful
            self.physiology_metrics['digestion_heat']+=e-useful
            s.gut_energy_weight=max(0.,s.gut_energy_weight-e)
            s.gut_quality_weight=max(0.,s.gut_quality_weight-e*quality)
        self.physiology_metrics['digested_mass']+=q
        self.trait_metrics['trait_digest_events']+=1

    def _work(self, a, activity, effort=1.0):
        """Locomotor efficiency reduces actual work; endurance limits fatigue."""
        trait=self._trait(a); state=self._state(a)
        before=state.fatigue
        paid=super()._work(a, activity, effort=effort/trait.locomotion)
        if paid:
            increment=max(0.,state.fatigue-before)
            state.fatigue=min(1.,before+increment/trait.endurance)
            self.trait_metrics['trait_work_events']+=1
        return paid

    def _feed_stock(self, a, source, kind, dt=None):
        """Feeding-capacity trait changes intake rate, not food energy density."""
        dt=getattr(self,'_current_dt',1.) if dt is None else dt
        result=super()._feed_stock(a,source,kind,dt=dt*self._trait(a).intake)
        if result:self.trait_metrics['trait_meals']+=1
        return result

    def _move_with_duration(self,a,action,t):
        moved=super()._move_with_duration(a,action,t)
        if moved:
            st=self._state(a)
            st.motion_ready_at=t+(st.motion_ready_at-t)/self._trait(a).locomotion
        return moved

    def _choose(self, a):
        """Trait-informed local vigilance, without omniscient global threat flags."""
        decision,hunger,danger=super()._choose(a)
        if a.stage=='dependent' or decision in ('sleep','flee'):
            return decision,hunger,danger
        if not self.eco_flags.spatial:
            return decision,hunger,danger
        radius=2 if self._trait(a).vigilance>=1.12 else 1
        nearby=False
        here=self._pos(a)
        for hunter in self.actors.values():
            if not hunter.alive or hunter.id==a.id or hunter.habitat!=a.habitat:
                continue
            if a.species not in PREY.get(hunter.species,()):
                continue
            their=self._pos(hunter)
            if abs(here[1]-their[1])+abs(here[2]-their[2])<=radius:
                nearby=True
                break
        if nearby and not danger and self._state(a).fatigue<.80:
            self.trait_metrics['vigilance_detected_threat']+=1
            if a.species in ('red_fox','golden_jackal','insectivore_shrew'):
                return 'flee',hunger,True
            if hunger<.65:return 'hide',hunger,True
        return decision,hunger,danger

    def _hunt(self,a):
        """Sensing/coordination phenotype affects capture through existing code."""
        trait=self._trait(a)
        base_skill=a.hunt_skill
        a.hunt_skill=min(1.,max(0.,base_skill*trait.sense))
        try:return super()._hunt(a)
        finally:
            # Preserve any earned experience rather than resetting on a kill.
            gain=max(0.,a.hunt_skill - min(1.,base_skill*trait.sense))
            a.hunt_skill=min(1.,base_skill+gain)

    def _reproduce(self):
        """Existing resource gates retained; heritable fecundity only changes
        conception probability after mate access and maternal funding checks.
        """
        phase=self.day%YEAR
        for mom in list(self.actors.values()):
            if not mom.alive or mom.sex!='F':continue
            p=PROFILES[mom.species]
            if mom.pregnant_until is not None:
                if self.day>=mom.pregnant_until:self._birth(mom)
                continue
            if mom.stage!='adult' or not(p.breeding[0]<=phase<=p.breeding[1]):continue
            if mom.condition<.65 or self.book.mass[self.physical.live(mom)]<p.adult_mass()*.70:continue
            if self.day-mom.last_birth_day<p.gestation+p.independence:continue
            if self.book.mass[self.physical.maternal(mom)]<p.birth_cost*MASS_SCALE:continue
            if self.book.energy[self.physical.reserve(mom)]<.012:continue
            mates=[x for x in self.actors.values() if x.alive and x.id!=mom.id and
                   x.species==mom.species and x.sex=='M' and x.stage=='adult' and
                   x.habitat==mom.habitat and x.condition>=.65]
            if not mates:continue
            if self.rng.random()>=min(1.,.042*self._trait(mom).reproductive):continue
            father=self.rng.choice(mates)
            mom.pregnancy_father=father.id; mom.pregnant_until=self.day+p.gestation
            self._log('conception',mother=mom.id,father=father.id,due=mom.pregnant_until,
                      species=mom.species,maternal_stock=self.book.mass[self.physical.maternal(mom)])
            self.trait_metrics['trait_conceptions']+=1

    def _birth(self,mom):
        father=self.actors.get(mom.pregnancy_father)
        older=set(self.actors)
        born=super()._birth(mom)
        if born:
            for child in self.actors.values():
                if child.id in older or child.parent!=mom.id:continue
                rng=Random(stable_seed(self.seed, child.id,'inheritance-144'))
                self.phenotypes[child.id]=descendant_phenotype(
                    child.species, self._trait(mom), self._trait(father) if father else None, rng)
                self.trait_metrics['inherited_offspring']+=1
        return born


class CoreCompletionWorld144(CoreCompletionWorld143):
    """Native residents share paired food and a physically circulating watershed."""
    # All are synthetic flux bounds in existing Book mass units. Hydrology is
    # a catchment-scale environmental mechanism, NOT a resource grant to actors.
    CLOUD_HOLD=5.0
    CONVECTIVE_FRACTION=.065
    MAX_RECHARGE_PER_HABITAT=.36
    RAIN_WEIGHTS={'forest':1.1,'grassland':1.,'wetland':1.15,
                  'ridge':.70,'floodplain':1.20}

    def _climate_and_plants(self):
        super()._climate_and_plants()
        cloud=f'water:tree:{self.id}:cloud'
        book=self.book
        excess=max(0.,book.mass[cloud]-self.CLOUD_HOLD)
        climate_factor=max(0.,getattr(self,'precipitation_factor',1.0))
        if excess<=1e-9 or climate_factor<=0:return
        # Increasing cloud water raises the chance/strength of precipitation.
        # Slow catchment redistribution prevents water from being permanently
        # stranded in the shared cloud due to fixed seasonal precipitation.
        q=min(excess, excess*self.CONVECTIVE_FRACTION*climate_factor,
              self.MAX_RECHARGE_PER_HABITAT*len(self.habitats))
        if q<=1e-9:return
        weights={h:self.RAIN_WEIGHTS.get(h,1.) for h in self.habitats}
        total=sum(weights.values())
        moves=[(cloud,self.acct('water',h),q*w/total) for h,w in weights.items()]
        txn=book.move(material=moves)
        self.counters['cloud_precipitation_events']+=1
        self.counters['cloud_precipitation_mass']+=q
        self.last_txn=txn

    def _migrate(self,r):
        p=r.habitat
        neighbors=tuple(self.habitats[p].neighbors)
        counts=Counter(x.habitat for x in self.residents.values() if x.alive)
        def capacity(h):
            lot=self._five_phase_inventory.plant(h)
            return self._five_phase_inventory.available_mass(lot)/(1+counts[h])
        current=capacity(p)
        best=max(neighbors,key=lambda h:(capacity(h),h))
        if capacity(best)<=max(.015,current*1.13):return False
        if (self.migration_cooldown_days>0 and
            self.age-r.last_migration_age<self.migration_cooldown_days and r.health>=.40):
            self.counters['tree_migration_deferred']+=1
            return False
        met=f'metabolic:{r.id}';cost=.008
        if self.book.energy[met]+1e-12<cost:return False
        txn=self.book.move(energy=[(met,self.acct('heat',p),cost)])
        r.habitat=best;r.last_migration_age=self.age;r.last_migration_origin=p
        self.last_txn=txn
        self._event('tree_migration',actor=r.id,txn=txn,habitat=best,
                    from_habitat=p,reason='edible_resource_access')
        self.counters['edible_resource_migrations']+=1
        return True

    def _animals(self):
        """Retain native demographic rules, but remove outdated chem hunger cue."""
        from random import Random
        present=[r for r in self.residents.values() if r.alive]
        rng=Random(stable_seed(self.sim.seed,self.id,self.age,'life'))
        rng.shuffle(present)
        pending=[]
        for r in present:
            r.age+=1
            if getattr(self,'disease_risk',0)>0 and rng.random()<self.disease_risk:
                r.health=max(0.,r.health-.25)
                self._event('tree_disease',actor=r.id,habitat=r.habitat)
            if r.age>r.max_age or r.health<=0:
                self._death(r,'old_age' if r.age>r.max_age else 'starvation');continue
            h=r.habitat
            lot=self._five_phase_inventory.plant(h)
            local_edible=self._five_phase_inventory.available_mass(lot)
            competitors=sum(x.alive and x.habitat==h for x in present)
            if local_edible/(1+competitors)<.25:
                self._migrate(r)
            h=r.habitat
            self._feed(r);self._metabolism(r)
            if r.health<=0:self._death(r,'starvation');continue
            pop=self.population
            cap=min(65,max(8,int(sum(self.book.mass[self.acct('plant',k)] for k in self.habitats)*1.75)))
            plant=self.book.mass[self.acct('plant',h)]
            readiness=(r.age>=14 and self.age-r.last_birth>=9 and
                       self.book.mass[f'fuel:{r.id}']>=.17 and
                       self.book.energy[f'metabolic:{r.id}']>=.028 and
                       r.health>=.65 and plant>=.40 and pop<cap)
            if readiness and rng.random()<.075*max(.04,1-pop/cap):pending.append(r)
        for parent in pending:
            if (parent.alive and self.book.mass[f'fuel:{parent.id}']>=.145 and
                self.book.energy[f'metabolic:{parent.id}']>=.023):
                self._new_resident(parent.habitat,parent=parent)
        self.counters['tree_population_tick']+=1

    def _native_absorb(self,r):
        """Native and bridge share the same gut-rate mathematical kernel."""
        b=self.book;gut=self._native_gut(r);ge=self._native_gut_energy(r)
        gm=b.mass[gut]
        if gm<=1e-12:return 0.
        q=gm*fraction_over_elapsed(SHARED_ABSORPTION_RATE,1.)
        e=b.energy[ge]*q/max(gm,1e-12)
        useful=e*NATIVE_ASSIMILATION_FRACTION
        work=q*.0005
        metabolic=f'metabolic:{r.id}'
        if b.energy[metabolic]+1e-12<work:return 0.
        b.transform([(gut,f'fuel:{r.id}',q)],source=metabolic,work=work,
             energy_outputs=[(metabolic,self.acct('heat',r.habitat),work*.9),
                             (ge,metabolic,useful),
                             (ge,self.acct('heat',r.habitat),e-useful)])
        self.counters['native_absorption_events']+=1
        self.counters['native_absorbed_energy']+=useful
        return useful


class FounderWorldSupport144:
    """Mixin: bounded Founder-backed structure topups + existing producer support."""
    STRUCTURAL_HORIZON_DAYS=6.
    MAX_STRUCTURE_PER_DAY=.65

    def maintain(self):
        production_paid=super().maintain()
        world=self.world;registry=self.society.seeds.constructs
        if world.state not in ('active','germinating'):
            return production_paid
        remaining=self.MAX_STRUCTURE_PER_DAY
        used={}
        for cid in (world.id,world.realm_id):
            c=registry.items.get(cid)
            if c is None or c.status!='stable' or c.daily_energy<=0:continue
            current=self.book.energy[f'reserve:{cid}']
            target=c.daily_energy*self.STRUCTURAL_HORIZON_DAYS
            need=min(max(0.,target-current),remaining)
            if need<=1e-10:continue
            moves=[]
            for fid,available in self._donors():
                room=max(0.,self.policy.max_contribution-used.get(fid,0.))
                q=min(need,room,max(0.,available-used.get(fid,0.)))
                if q<=1e-10:continue
                moves.append((f'founder:{fid}',f'reserve:{cid}',q))
                used[fid]=used.get(fid,0.)+q
                need-=q
                if need<=1e-10:break
            if moves:
                txn=self.book.move(energy=moves)
                delivered=sum(q for _,_,q in moves)
                remaining-=delivered
                self.totals['structure_energy']+=delivered
                self.totals['structure_transactions']+=1
                self.events.append({'day':self.engine.days,'purpose':'structural_upkeep',
                                    'construct':cid,'energy':delivered,'book_seq':txn.seq})
            elif need>1e-8:self.totals['structure_unfunded']+=1
            if remaining<=1e-10:break
        return production_paid + (self.MAX_STRUCTURE_PER_DAY-remaining)


class UnifiedCoreCompletion144(UnifiedCoreCompletion143):
    """Versioned candidate; inherit Core143 world/clock and make real changes."""
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if type(self.bridge) is not CoreCompletionBridge143:
            raise TypeError('Cycle144 expected untouched Core143 active bridge')
        if type(self.bridge.tree) is not CoreCompletionWorld143:
            raise TypeError('Cycle144 expected untouched Core143 active World Tree')
        self.bridge.__class__=CoreCompletionBridge144
        self.bridge.activate_traits()
        self.bridge.tree.__class__=CoreCompletionWorld144
        self.bridge.lots=EcologicalProduction144(self.bridge)
        self.bridge.tree._five_phase_inventory=self.bridge.lots
        self.bridge.lots.balance_all()
        if self.world_support is not None:
            # Same policy, donor eligibility and Book; no second scheduler.
            # Pickle must resolve a globally named class.
            self.world_support.__class__=WorldSupport144
        self._check()

    def report(self):
        report=super().report()
        report['core_completion_144']={
            'status':'experimental_not_canonical',
            'traits_active':True,
            'species_profiles':len(BLUEPRINTS),
            'individual_trait_count':len(self.bridge.phenotypes),
            'trait_metrics':dict(self.bridge.trait_metrics),
            'native_edible_migrations':self.bridge.tree.counters['edible_resource_migrations'],
            'photosynthetic_capture':self.bridge.lots.metrics['photosynthetic_capture_energy'],
            'cloud_precipitation_mass':self.bridge.tree.counters['cloud_precipitation_mass'],
            'one_book':self.host.book is self.bridge.book is self.bridge.tree.book,
            'founder_funded_structure':self.world_support is not None,
        }
        return report

# Stable globally addressable class to preserve pickle/cloud-to-local replay.
from five_phase_core_142 import MechanismAwareWorldFunding142
class WorldSupport144(FounderWorldSupport144, MechanismAwareWorldFunding142):
    pass
