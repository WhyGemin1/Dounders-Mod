"""Cycle138 opt-in bounded ecological mechanisms on Cycle135 Unified260.

M: extra climate-limited material transformations in the *existing* WorldTree Book.
S: one-step, energy-paid microcell locomotion, prey-range restriction, non-owning
   Book-backed plant/carrion allocation quotas (never a second inventory).
J: physical caregiver meals for dependents and juvenile food-search preference.
All parameters below are synthetic research probes, NOT empirical calibration.
No source default is mutated, no additional actor scheduler or Book is created.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
import math
from integrated_02160 import Unified260
from knowledge_family_02142 import KnowledgeFamilyBridge242
from species_life_02115 import PROFILES, PREY
from digestion_02120 import PLANT_DIGESTIBILITY, CARRION_DIGESTIBILITY

HERBIVORES=('field_mouse','meadow_grazer','forest_browser')
CELL_COST=.00012
CARE_WORK=.00012
CARE_GIFT=.00018

@dataclass(frozen=True)
class EcoFlags:
    metabolism:bool=False
    spatial:bool=False
    juvenile:bool=False

class EcoBridge138(KnowledgeFamilyBridge242):
    """Installed by __class__ promotion *after* unmodified baseline bootstrap.

    All-off dispatches exactly to original Cycle135 methods; the original RNG
    stream is not consumed by a disabled option.
    """
    def activate(self, flags):
        self.eco_flags=flags
        self.eco_metrics=Counter()
        self._cell_quota={}
        self._quota_day=-1
        self._child_fed_day={}

    def _pos(self,a):
        # Positions are originally diagnostic only, but spatial arm uses them.
        if a.id not in self.positions:self.sync_positions()
        return self.positions[a.id]

    def _neighbors(self,cell):
        h,x,y=cell; z=self.grid_size
        return [(h,x+dx,y+dy) for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))
                if 0<=x+dx<z and 0<=y+dy<z]

    def _cell_weight(self,h,x,y,kind):
        # Fixed, heterogeneous spatial productivity; not empirical habitat data.
        # More than 50% weight variation prevents a uniform-resource fiction.
        rank=((x*17+y*31+len(h)*13+self.seed*7) % 19)
        return (0.2+rank/12) if kind=='plant' else (0.1+(18-rank)/12)

    def _refresh_quota(self):
        if not self.eco_flags.spatial:return
        if self._quota_day==self.day:return
        self._cell_quota={}
        z=self.grid_size
        for h in self.tree.habitats:
            for kind,source in (('plant',self.tree.acct('plant',h)),('carrion',self.carrion(h))):
                total=self.book.mass[source]
                # The per-day envelope is *less* than the actual stock. Native
                # consumers and other transformations may debit the Book too.
                accessible=total*.42
                weight_sum=sum(self._cell_weight(h,x,y,kind) for x in range(z) for y in range(z))
                for x in range(z):
                    for y in range(z):
                        key=(source,h,x,y)
                        self._cell_quota[key]=accessible*self._cell_weight(h,x,y,kind)/weight_sum
                assert sum(v for (s,*_),v in self._cell_quota.items() if s==source) <= total+1e-8
        self._quota_day=self.day
        self.eco_metrics['quota_refreshes']+=1

    def _local_quota(self,a,source):
        if not self.eco_flags.spatial:return float('inf')
        self._refresh_quota()
        return self._cell_quota.get((source,*self._pos(a)), 0.)

    def _local_access(self,a,source):
        # The Book remains authoritative even if other consumers have spent
        # account stock after the quotas were generated.
        return min(self.book.mass[source],self._local_quota(a,source))

    def _feed_stock(self,a,source,kind):
        if not (self.eco_flags.spatial or (self.eco_flags.juvenile and a.parent and a.age<PROFILES[a.species].maturity)):
            return super()._feed_stock(a,source,kind)
        # Keep the complete Cycle135 embodied-tissue-energy accounting from
        # HabitatBridge220._feed_stock; only its local q budget and age intake
        # are experimental. Never replace real digestion by free reserve gain.
        p=PROFILES[a.species];b=self.book;ph=self.physical
        before_energy=b.energy[ph.reserve(a)]
        young=bool(self.eco_flags.juvenile and a.parent and a.age<p.maturity)
        fraction=(.65+.35*min(1.,a.age/p.maturity)) if young else 1.
        carrion=(source==self.carrion(a.habitat))
        q=min(p.intake*.012*fraction,self._local_access(a,source))
        chem=ph.chem(a)
        if not carrion:q=min(q,max(0.,b.energy[chem]/.80))
        if q<.0004:
            if self.eco_flags.spatial and b.mass[source]>.0004:
                self.eco_metrics['spatial_food_blocked']+=1
            return False
        before_mass=b.mass[source]
        target=p.adult_mass()*(.35+.65*min(1.,a.age/p.maturity))
        growth=min(q*.17,max(0.,target-b.mass[ph.live(a)])) if a.age<p.maturity else 0.
        store=(min(q*.22,max(0.,p.maternal_cap()-b.mass[ph.maternal(a)]))
               if a.sex=='F' and a.stage=='adult' else 0.)
        rest=max(0.,q-growth-store)
        legs=[]
        for account,amount in ((ph.live(a),growth),(ph.maternal(a),store),(ph.gut(a),rest)):
            if amount>1e-12:legs.append((source,account,amount))
        ph.convert(legs)
        if carrion:
            origin=ph.carrion_energy(a.habitat)
            intake=min(b.energy[origin],b.energy[origin]*q/max(before_mass,1e-12))
            efficiency=CARRION_DIGESTIBILITY
        else:
            origin=chem
            intake=min(b.energy[origin],q*.80)
            efficiency=PLANT_DIGESTIBILITY
        digestible=intake*efficiency
        tissue=digestible*growth/q
        maternal=digestible*store/q
        reserve=max(0.,digestible-tissue-maternal)
        heat=intake-digestible
        transfers=[(origin,dest,amount) for dest,amount in
                   ((ph.tissue(a),tissue),(ph.maternal_energy(a),maternal),
                    (ph.reserve(a),reserve),('environment:heat',heat)) if amount>1e-12]
        if transfers:b.move(energy=transfers)
        gut=b.mass[ph.gut(a)]
        if gut>1e-12:ph.convert([(ph.gut(a),ph.detritus(a),gut)])
        self.fluxes[f'{kind}_intake_energy']+=intake
        self.fluxes[f'{kind}_digestible_energy']+=digestible
        self.fluxes[f'{kind}_heat']+=heat
        if self.eco_flags.spatial:
            key=(source,*self._pos(a))
            self._cell_quota[key]-=q
            assert self._cell_quota[key]>=-1e-9
            self.eco_metrics['local_meal_mass']+=q
            self.eco_metrics['local_meals']+=1
        if young:
            self.eco_metrics['juvenile_growth_mass']+=growth
            self.eco_metrics['juvenile_meals']+=1
        self._log('feeding',actor=a.id,habitat=a.habitat,food_source=kind,mass=q,
                  growth=growth,maternal_mass=store,energy_intake=intake,
                  energy_digested=digestible,energy_to_heat=heat)
        if a.species=='ridge_hound':
            self._store_fat(a,before_energy)
        return True

    def _feed_herbivore(self,a):
        if self.eco_flags.spatial and self._local_access(a,self.physical.plant(a))<.0004:
            self.eco_metrics['local_herbivore_unavailable']+=1
            return False
        return super()._feed_herbivore(a)

    def _feed_scavenger(self,a):
        if not self.eco_flags.spatial:return super()._feed_scavenger(a)
        # Preserve existing carrion-first, even-day plant-fallback rules.
        carrion=self.carrion(a.habitat)
        if self._local_access(a,carrion)>.0004:
            return self._feed_stock(a,carrion,'carrion')
        source=self.physical.plant(a)
        if self.day%2==0 and self._local_access(a,source)>.0004:
            return self._feed_stock(a,source,'plant_fallback')
        self.eco_metrics['local_scavenger_unavailable']+=1
        return False

    def _hunt(self,a):
        if not self.eco_flags.spatial:return super()._hunt(a)
        if a.species not in PREY:return False
        px=self._pos(a)
        # An undetectable prey in another cell cannot be chosen by the
        # original habitat-wide hunt code. No prediction of hidden map cells.
        # Filtering the actor view only around one call avoids changing the
        # Book or other actor registry structures.
        visible=[x for x in self.actors.values() if x.alive and x.id!=a.id
                 and x.species in PREY[a.species] and x.habitat==a.habitat
                 and sum(abs(px[i]-self._pos(x)[i]) for i in (1,2))<=1]
        if not visible:
            self.eco_metrics['local_hunt_blocked']+=1
            return False
        # Existing hunt routines query self.actors. Temporarily use a view,
        # restore it in finally even if a Book operation throws. Never
        # permanently edit the authoritative registry.
        original=self.actors
        scoped={uid:x for uid,x in original.items()
                if x.id==a.id or x.species not in PREY[a.species]
                or x in visible}
        try:
            self.actors=scoped
            result=super()._hunt(a)
        finally:
            # A killed prey may have caregivers in the full actor registry.
            killed={x.id for x in visible if not x.alive}
            self.actors=original
            if killed:
                for other in original.values():
                    other.caregiver_ids.difference_update(killed)
        if result:self.eco_metrics['local_hunt_success']+=1
        return result

    def _migrate(self,a,decision=None):
        if not self.eco_flags.spatial:return super()._migrate(a,decision)
        old_h=a.habitat
        # Do not cause uncosted habitat jumps or override original cues.
        result=super()._migrate(a,decision)
        if old_h!=a.habitat:
            self.sync_positions()
            self.eco_metrics['habitat_moves']+=1
            return result
        if a.stage=='dependent' or decision in ('care','mate','rest','stay_with_caregiver'):
            return result
        here=self._pos(a);neighbors=self._neighbors(here)
        if not neighbors:return result
        reserve=self.physical.reserve(a)
        if self.book.energy[reserve]<CELL_COST+.0005:
            self.eco_metrics['cell_move_unfunded']+=1
            return result
        # Local sensory perception (cell plus adjacent cells) only.
        if a.species in PREY:
            prey_cells={self._pos(x) for x in self.actors.values() if x.alive
                        and x.habitat==a.habitat and x.species in PREY[a.species]}
            ranked=[(int(cell in prey_cells),cell) for cell in neighbors]
        else:
            source=(self.carrion(a.habitat) if a.species=='carrion_bird' else self.physical.plant(a))
            ranked=[(self._cell_quota.get((source,*cell),0.),cell) for cell in neighbors]
        # Explore locally, never seek a globally mapped distant food cache.
        score=max(v for v,_ in ranked)
        best=[cell for v,cell in ranked if v==score]
        target=best[(self.day+int(a.id.rsplit('-',1)[-1]))%len(best)]
        self.book.move(energy=[(reserve,'environment:heat',CELL_COST)])
        self.positions[a.id]=target
        self.eco_metrics['cell_moves']+=1
        self.eco_metrics['cell_move_energy_paid']+=CELL_COST
        self._log('cell_move',actor=a.id,habitat=a.habitat,from_cell=here[1:],
                  to_cell=target[1:],energy_cost=CELL_COST)
        # A dependent travels with its caregiver, not independently.
        for child in self.actors.values():
            if child.alive and child.stage=='dependent' and a.id in child.caregiver_ids and child.habitat==a.habitat:
                self.positions[child.id]=target
        return True

    def evaluate_needs(self,a):
        action,hunger,danger=super().evaluate_needs(a)
        if not self.eco_flags.juvenile or not a.parent or a.stage!='juvenile':return action,hunger,danger
        if a.species not in HERBIVORES:return action,hunger,danger
        if action in ('hide','flee') or hunger<.3:return action,hunger,danger
        if self._local_access(a,self.physical.plant(a))>.0004:
            if self.needs_last.get(a.id)!= 'feed':
                # This is an active behavior change, not just a report counter.
                prior=self.needs_last.get(a.id)
                if prior is not None:self.needs_choices[f'{a.species}:{prior}']-=1
                self.needs_choices[f'{a.species}:feed']+=1
                self.needs_last[a.id]='feed'
            self.eco_metrics['juvenile_feed_priority']+=1
            return 'feed',hunger,danger
        return action,hunger,danger

    def _care(self,a,episode='primary'):
        result=super()._care(a,episode=episode)
        if not self.eco_flags.juvenile:return result
        if a.stage not in ('adult','elder'):return result
        for child in tuple(self.actors.values()):
            if not (child.alive and child.stage=='dependent' and
                    a.id in child.caregiver_ids and child.habitat==a.habitat):continue
            if self._child_fed_day.get(child.id)==self.day:continue
            if self.eco_flags.spatial and self._pos(child)!=self._pos(a):continue
            donor=self.physical.reserve(a)
            if self.book.energy[donor] < .008+CARE_WORK+CARE_GIFT:continue
            source=(self.carrion(a.habitat) if a.species in ('ridge_hound','carrion_bird')
                    else self.physical.plant(a))
            if self._local_access(a,source)<.0004:continue
            before=self.book.mass[self.physical.live(child)]
            # Source and chemical energy are debited by established feeding
            # mechanics; donor adds physically funded labor plus care energy.
            if not self._feed_stock(child,source,'caregiver_provision'):continue
            self.book.move(energy=[(donor,'environment:heat',CARE_WORK),
                                   (donor,self.physical.reserve(child),CARE_GIFT)])
            self.eco_metrics['caregiver_meals']+=1
            self.eco_metrics['caregiver_work_paid']+=CARE_WORK
            self.eco_metrics['caregiver_energy_given']+=CARE_GIFT
            self.eco_metrics['caregiver_child_growth']+=self.book.mass[self.physical.live(child)]-before
            self._log('caregiver_meal',actor=a.id,child=child.id,food_source=source,
                      work=CARE_WORK,energy=CARE_GIFT)
            self._child_fed_day[child.id]=self.day
        return result

    def step(self,tick):
        if self.eco_flags.spatial:
            # day label set before actor loop for quota refresh, then parent
            # advances its regular scheduler exactly once.
            self.day=tick
            self._refresh_quota()
            self.day=tick-1
        return super().step(tick)

    def eco_summary(self):
        return {k:round(v,9) for k,v in sorted(self.eco_metrics.items())}

class UnifiedEcoFactorial138(Unified260):
    """Same World Tree, one Book, one host step and one bridge step per day."""
    def __init__(self,seed=9711,*,metabolism=False,spatial=False,juvenile=False,**kwargs):
        for key,value in [('metabolism',metabolism),('spatial',spatial),('juvenile',juvenile)]:
            if type(value) is not bool:raise TypeError(key+' must be bool')
        super().__init__(seed=seed,**kwargs)
        self.eco_flags=EcoFlags(metabolism,spatial,juvenile)
        if not isinstance(self.bridge,KnowledgeFamilyBridge242):
            raise TypeError('unexpected bridge type; fail closed')
        self.bridge.__class__=EcoBridge138
        self.bridge.activate(self.eco_flags)
        self.eco_flux=Counter()
        self._check()

    def _extra_metabolism(self):
        tree=self.bridge.tree;book=self.host.book
        if tree.state not in ('active','germinating'):return
        for h in tree.habitats:
            sun=tree.acct('sun',h)
            water=book.mass[tree.acct('water',h)]
            soil=book.mass[tree.acct('soil',h)]
            daylight=book.energy[sun]
            wet=tree.habitats[h].season=='wet'
            moisture=min(1.,water/2.)
            light=min(1.,daylight/.6)
            seasonal=.85 if wet else .50
            if h=='ridge':seasonal*=.65
            if h=='wetland':seasonal*=min(1.,water/1.4)
            if h=='floodplain':seasonal*=min(1.,water/1.2)
            # Gross conversion and litter both compete for finite light work.
            det=book.mass[tree.acct('detritus',h)]
            decay=min(det*.018*moisture, .013)
            if decay>1e-8 and book.energy[sun] >= decay*.025+1e-8:
                txn=tree._material_change('detritus','soil',h,decay,sun,.025)
                if txn is not None:
                    self.eco_flux['detritus_to_soil']+=decay
                    self.eco_flux['decomposition_events']+=1
            litter=min(book.mass[tree.acct('plant',h)]*.0012,.009)
            if litter>1e-8 and book.energy[sun] >= litter*.025+1e-8:
                txn=tree._material_change('plant','detritus',h,litter,sun,.025)
                if txn is not None:
                    self.eco_flux['litter_mass']+=litter
                    self.eco_flux['litter_events']+=1
            # Actual finite resource limits, no added sunlight/soil/water.
            growth=min(.022*moisture*light*seasonal,book.mass[tree.acct('soil',h)]*.012,
                       max(0.,book.energy[sun]/.30))
            if growth>1e-8:
                work=growth*.30
                book.transform([(tree.acct('soil',h),tree.acct('plant',h),growth)],
                               source=sun,work=work,
                               energy_outputs=[(sun,tree.acct('chem',h),work*.9)])
                self.eco_flux['new_growth_mass']+=growth
                self.eco_flux['new_growth_events']+=1
        book.audit()

    def step(self):
        if not self.eco_flags.metabolism:
            return super().step()
        # Identical host step as legacy, with a physically funded M process
        # after native ecology and before bridge consumers. This is explicitly
        # additional limited metabolism, not replacing native plant scheduler.
        self.host.step();self.days+=1
        self._extra_metabolism()
        self.bridge.step(self.days)
        self._check()
        if self.days==1 or self.days%30==0:
            self.history.append({'day':self.days,'species':self.bridge.report(),
              'tree_state':self.bridge.tree.state,'tree_population':self.bridge.tree.population,
              'tree_plant_mass':sum(self.host.book.mass[self.bridge.tree.acct('plant',p)]
                                for p in self.bridge.tree.habitats),
              'ledger':self.host.book.audit()})

    def report(self):
        result=super().report()
        result['eco_factorial_138']={
            'M':self.eco_flags.metabolism,'S':self.eco_flags.spatial,'J':self.eco_flags.juvenile,
            'experimental':True,'metabolism_fluxes':dict(self.eco_flux),
            'bridge_activation':self.bridge.eco_summary()}
        return result
