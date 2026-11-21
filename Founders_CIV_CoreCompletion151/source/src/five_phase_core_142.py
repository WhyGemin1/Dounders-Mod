"""Cycle142 five-phase ecological repair -- unified experimental candidate.

This is a real adapter on the World Tree and its existing Book, not a second
simulation or a replacement material ledger. Parameters remain synthetic;
full empirical/ecological validation is a separate release gate.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from math import exp, isfinite
from founders_civ.experimental.world_trees import WorldTree

from core_physiology_v2 import (UnifiedCoreV2, PhysiologyBridgeV2,
    FunctionalState, _temporary_diet_registry, PROFILES, PREY, COVER, ANTS, MEGA,
    MIN_QUEEN_MASS, CARRION_DIGESTIBILITY, PLANT_DIGESTIBILITY, YEAR)
from founder_world_energy_141 import FounderWorldSupport141

# Book units remain historical, dimensionless simulation units. Calibrate later.
PLANT_EDIBLE_ENERGY_DENSITY = .30
ANIMAL_TISSUE_ENERGY_DENSITY = .45
ADULT_INTAKE_MULTIPLIER = .095
N_SUBSTEPS = 4  # Numerical resolution of overlapping physical processes; NOT action credits.
MIN_WORK = 1e-9


@dataclass(frozen=True)
class EdibleLot:
    """A view of Book-owned material and energy accounts; no duplicate inventory."""
    mass_account: str
    energy_account: str
    habitat: str
    material: str
    nominal_density: float


class EdibleInventory142:
    """Bind existing plant biomass to energy actually held in Book accounts."""
    def __init__(self, bridge):
        self.bridge = bridge
        self.metrics = Counter()

    def plant(self, habitat):
        t = self.bridge.tree
        return EdibleLot(t.acct('plant', habitat),
                         f'edible_energy:tree:{t.id}:{habitat}', habitat,
                         'producer_plant', PLANT_EDIBLE_ENERGY_DENSITY)

    def carrion(self, habitat):
        b = self.bridge
        return EdibleLot(b.carrion(habitat), b.physical.carrion_energy(habitat),
                         habitat, 'animal_carrion', ANIMAL_TISSUE_ENERGY_DENSITY)

    def detritus(self, habitat):
        t = self.bridge.tree
        return EdibleLot(t.acct('detritus', habitat),
                         f'detritus_energy:tree:{t.id}:{habitat}', habitat,
                         'dead_organic_matter', .16)

    def balance(self, habitat):
        """Reconcile old native production into a paired accessible energy lot.

        Historic chemical energy is a SOURCE of embodied nutrients, not a second
        claim on each plant meal. Not enough chemical source means food scarcity;
        we do NOT assign free energy merely because plant mass exists.
        """
        b = self.bridge.book; t = self.bridge.tree
        lot = self.plant(habitat)
        mass = b.mass[lot.mass_account]; currently = b.energy[lot.energy_account]
        target = mass * lot.nominal_density
        if currently > target + 1e-10:
            excess = currently-target
            b.move(energy=[(lot.energy_account, self.detritus(habitat).energy_account, excess)])
            self.metrics['energy_reassigned_to_detritus'] += excess
        elif currently + 1e-10 < target:
            chem = t.acct('chem', habitat)
            available = b.energy[chem]
            contribution = min(target-currently,available)
            if contribution > 1e-10:
                b.move(energy=[(chem,lot.energy_account,contribution)])
                self.metrics['producer_energy_packaged'] += contribution
        self.metrics['producer_reconciliations'] += 1

    def balance_all(self):
        for h in self.bridge.tree.habitats:self.balance(h)

    def available_mass(self, lot):
        b = self.bridge.book
        mass = b.mass[lot.mass_account]
        embodied = b.energy[lot.energy_account]
        return min(mass, embodied / max(lot.nominal_density,1e-12))

    def ingest(self, animal, lot, mass, quality, name):
        """One atomic Book transformation debits matching mass and food energy."""
        b = self.bridge.book; br = self.bridge
        self.balance(lot.habitat) if lot.material == 'producer_plant' else None
        q = min(max(0.,mass), self.available_mass(lot))
        if q < 1e-6:return False
        source_sun = br.tree.acct('sun', lot.habitat)
        work = max(1e-8, q*.001)
        if b.energy[source_sun] < work:return False
        energy = q*lot.nominal_density
        # Fixed density is intentional: no unaccounted zero-calorie mass.
        if b.energy[lot.energy_account]+1e-10 < energy:return False
        txn = b.transform([(lot.mass_account, br.physical.gut(animal),q)],
            source=source_sun,work=work,
            energy_outputs=[(source_sun, 'environment:heat', work*.90),
                            (lot.energy_account,br._gut_energy(animal),energy)])
        s = br._state(animal)
        s.gut_energy_weight += energy
        s.gut_quality_weight += energy*quality
        br.physiology_metrics['ingested_mass'] += q
        br.physiology_metrics['ingested_energy'] += energy
        br.physiology_metrics['paired_lot_meals'] += 1
        if br.eco_flags.spatial:
            br._spend_forage_quota(animal, lot.mass_account, q)
        br._log('feeding',actor=animal.id,habitat=animal.habitat,food_source=name,
                mass=q,into_gut_energy=energy,absorbed_immediately=0.,book_seq=txn.seq)
        return True


def native_paired_feed_142(tree, r):
    """Top-level native feeding function so checkpoints rebind to copied state."""
    inventory=tree._five_phase_inventory
    h=r.habitat;lot=inventory.plant(h);b=tree.book
    inventory.balance(h)
    fuel=f'fuel:{r.id}';maximum=.34
    q=min(.06,max(0.,maximum-b.mass[fuel]),inventory.available_mass(lot))
    sun=tree.acct('sun',h)
    work=q*.012
    if q<=.001 or b.energy[sun] < work:return False
    fuel_gain=q*lot.nominal_density*.74
    txn=b.transform([(lot.mass_account,fuel,q)],source=sun,work=work,
        energy_outputs=[(sun,tree.acct('heat',h),work*.9),
          (lot.energy_account,f'metabolic:{r.id}',fuel_gain),
          (lot.energy_account,tree.acct('heat',h),q*lot.nominal_density-fuel_gain)])
    tree.last_txn=txn;tree.counters['tree_grazing']+=1
    tree.counters['native_paired_meals']+=1
    return True


class PairedWorldTree142(WorldTree):
    """Native World Tree consumes the shared paired edible inventory."""
    def _feed(self, resident):
        return native_paired_feed_142(self,resident)


class MechanismAwareWorldFunding142(FounderWorldSupport141):
    """Don't automatically fund sun when light is already plentiful.

    This is an accountable Founder eligibility/policy decision proxy, not full
    CommonsWorld autonomous social negotiation; no welfare guarantee.
    """
    def maintain(self):
        if not self.activation_complete:raise RuntimeError('funding not initialized')
        t=self.world;b=self.book
        depleted=[];sun_limited=[]
        for h in t.habitats:
            plant=self.engine.bridge.lots.plant(h)
            if b.energy[plant.energy_account] < b.mass[plant.mass_account]*.12:
                depleted.append(h)
                if b.energy[t.acct('sun',h)] < self.policy.critical_sun:
                    sun_limited.append(h)
        if not sun_limited:
            self.totals['diagnosed_non_solar_constraint']+=len(depleted)
            self.last_funding_day=self.engine.days+1
            return 0.
        self.totals['diagnosed_solar_shortage']+=len(sun_limited)
        return super().maintain()


class FivePhaseBridge142(PhysiologyBridgeV2):
    """Single active physiology dispatch; never call legacy bridge.step()."""
    def activate_five_phases(self, substeps=N_SUBSTEPS):
        if not 1 <= substeps <= 16:raise ValueError('invalid numerical resolution')
        self.substeps=substeps
        self.lots=EdibleInventory142(self)
        self.lots.balance_all()
        self.physiology_metrics['five_phase_activated']+=1
        self._install_native_edible_feeding()
        self._reconcile_animals()
        self._cohort_snapshot=[]

    def _reconcile_animals(self):
        """Finance edible tissue rather than pretending animals are empty calories."""
        b=self.book;t=self.tree;ph=self.physical
        for a in self.actors.values():
            mass=b.mass[ph.live(a)]
            target=mass*ANIMAL_TISSUE_ENERGY_DENSITY
            account=ph.tissue(a)
            gap=max(0.,target-b.energy[account])
            if gap<=1e-12:continue
            donor=t.acct('chem',a.habitat)
            available=b.energy[donor]
            q=min(gap, available)
            if q>1e-12:
                b.move(energy=[(donor,account,q)])
                self.physiology_metrics['funded_tissue_energy']+=q

    def _install_native_edible_feeding(self):
        """Native residents keep their distinct demographics but eat same lots."""
        native_tree=self.tree
        if getattr(native_tree,'_cycle142_feeding_installed',False):return
        native_tree._five_phase_inventory=self.lots
        native_tree.__class__=PairedWorldTree142
        native_tree._cycle142_feeding_installed=True

    def _digest(self,a,dt=1.):
        """Rate-based assimilation independent of sleep and chosen behavior."""
        b=self.book;ph=self.physical;s=self._state(a)
        gut=ph.gut(a);gm=b.mass[gut]
        if gm<=1e-12:return
        # Fraction assimilated in elapsed world time, not per action count.
        q=gm*(1.-exp(-.72*dt))
        ge=self._gut_energy(a); e=b.energy[ge]*q/max(gm,1e-12)
        p=PROFILES[a.species]
        target=p.adult_mass()*(.35+.65*min(1.,a.age/max(1,p.maturity)))
        grow=min(q*.12,max(0.,target-b.mass[ph.live(a)])) if a.age<p.maturity else 0.
        maternal=(min(q*.11,max(0.,p.maternal_cap()-b.mass[ph.maternal(a)]))
                   if a.sex=='F' and a.stage=='adult' else 0.)
        waste=max(0.,q-grow-maternal)
        material=[(gut,dest,n) for dest,n in ((ph.live(a),grow),
             (ph.maternal(a),maternal),(ph.detritus(a),waste)) if n>1e-12]
        if material:ph.convert(material)
        quality=max(0.,min(1.,s.gut_quality_weight/max(s.gut_energy_weight,1e-12)))
        if e>1e-12:
            useful=e*quality;energy_to_tissue=useful*grow/max(q,1e-12)
            energy_to_maternal=useful*maternal/max(q,1e-12)
            energy_to_short=useful-energy_to_tissue-energy_to_maternal
            transfers=[(ge,dst,n) for dst,n in
                ((ph.tissue(a),energy_to_tissue),
                 (ph.maternal_energy(a),energy_to_maternal),
                 (self._short(a),energy_to_short),('environment:heat',e-useful)) if n>1e-12]
            if transfers:b.move(energy=transfers)
            self.physiology_metrics['absorbed_energy']+=useful
            self.physiology_metrics['digestion_heat']+=e-useful
            s.gut_energy_weight=max(0.,s.gut_energy_weight-e)
            s.gut_quality_weight=max(0.,s.gut_quality_weight-e*quality)
        self.physiology_metrics['digested_mass']+=q

    def _metabolize(self,a,dt=1.):
        if not a.alive:return
        self._digest(a,dt)
        s=self._state(a);demand=self._maintenance_demand(a)*dt
        paid=self._consume_short(a,demand,'maintenance')
        if paid+1e-9<demand:
            deficiency=(demand-paid)/max(demand,1e-12)
            s.starvation_debt+=.07*dt*deficiency
            a.condition=max(0.,a.condition-.018*dt*deficiency)
        else:s.starvation_debt=max(0.,s.starvation_debt-.006*dt)
        self.physiology_metrics['metabolic_steps']+=1

    def _forage_cells(self,a,source):
        here=self._pos(a)
        if a.species in MEGA and source==self.tree.acct('plant',a.habitat):
            h,x,y=here
            return [here]+[(h,i,j) for i in range(max(0,x-1),min(self.grid_size,x+2))
                    for j in range(max(0,y-1),min(self.grid_size,y+2)) if (i,j)!=(x,y)]
        return [here]

    def _local_access(self,a,source):
        if not self.eco_flags.spatial:return self.book.mass[source]
        self._refresh_quota()
        return min(self.book.mass[source],sum(max(0.,self._cell_quota.get((source,*c),0.))
                    for c in self._forage_cells(a,source)))

    def _spend_forage_quota(self,a,source,amount):
        remainder=amount
        for cell in self._forage_cells(a,source):
            key=(source,*cell);available=max(0.,self._cell_quota.get(key,0.))
            paid=min(available,remainder)
            if paid:self._cell_quota[key]=available-paid;remainder-=paid
            if remainder<=1e-9:break
        if remainder>1e-7:raise AssertionError('forage quota exceeded')

    def _food_lot(self,a,source):
        if source==self.tree.acct('plant',a.habitat):return self.lots.plant(a.habitat)
        if source==self.carrion(a.habitat):return self.lots.carrion(a.habitat)
        if source==self.tree.acct('detritus',a.habitat):return self.lots.detritus(a.habitat)
        return None

    def _feed_stock(self,a,source,kind,dt=None):
        if not a.alive:return False
        # Legacy callers have no dt argument; they inherit the current world
        # integration interval, not a full day's food allowance EACH substep.
        dt=getattr(self,'_current_dt',1.) if dt is None else dt
        lot=self._food_lot(a,source)
        if lot is None:return False
        body=self._bodymass(a)
        intake_per_day=max(.008,body*.22 if body<.10 else
                                body*.14 if body<.5 else body*.075)
        if a.species==ANTS:intake_per_day*=.55
        if a.stage in ('dependent','juvenile'):intake_per_day*=.7
        q=min(intake_per_day*dt, self._local_access(a,source),
              max(0.,.28*body-self.book.mass[self.physical.gut(a)]))
        quality=(PLANT_DIGESTIBILITY if lot.material=='producer_plant'
                 else .30 if lot.material=='dead_organic_matter' else CARRION_DIGESTIBILITY)
        return self.lots.ingest(a,lot,q,quality,kind)

    def _ant_worker_take(self,a):
        """Worker feeding respects colony body mass and its tissue-energy density."""
        old=self._state(a)
        before=self.book.mass[self.physical.gut(a)]
        success=super()._ant_worker_take(a)
        if success and self.book.mass[self.physical.gut(a)]>before:
            self.physiology_metrics['ant_feeding_events']+=1
        return success

    def _choose(self,a):
        """Homeostatic feed/escape/rest decisions use energy throughput and gut."""
        st=self._state(a)
        if a.stage=='dependent':return 'stay_with_caregiver',0.,False
        if st.sleep_pressure>.76 and st.readiness<.70:return 'sleep',0.,False
        if st.fatigue>.70:return 'rest',0.,False
        heat=self._maintenance_demand(a)
        circulating=self.book.energy[self._short(a)]
        reserve=self.book.energy[self.physical.reserve(a)]
        gut=self.book.energy[self._gut_energy(a)]
        accessible=circulating+reserve*.45+gut*.40
        target=heat*18+self._bodymass(a)*.010
        hunger=max(0.,min(1.,(target-accessible)/max(target,1e-12)))
        # Presence somewhere in a large habitat is not perpetual mortal danger.
        # Concealment is triggered by local proximity, not global actor registry.
        predator_near = False
        for hunter in self.actors.values():
            if not (hunter.alive and hunter.habitat==a.habitat
                    and a.species in PREY.get(hunter.species,())):continue
            predator_near = (not self.eco_flags.spatial or
                sum(abs(self._pos(a)[i]-self._pos(hunter)[i]) for i in (1,2))<=1)
            if predator_near:break
        danger=predator_near
        if danger and a.species in ('red_fox','golden_jackal','insectivore_shrew'):
            return 'flee',hunger,True
        if danger and hunger<.50 and st.fatigue<.68:return 'hide',hunger,True
        if gut>heat*3 and circulating>heat*3 and st.fatigue>.28:
            return 'rest',hunger,bool(danger)
        if a.species in PREY or a.species=='carrion_bird':
            return ('feed' if hunger>.18 else 'rest'),hunger,bool(danger)
        return ('feed' if hunger>.18 else 'rest'),hunger,bool(danger)

    def _finish_behavior(self,a,behavior,dt=1.):
        s=self._state(a);s.last_behavior=behavior
        if behavior in ('rest','stay_with_caregiver'):
            s.fatigue=max(0.,s.fatigue-.14*dt)
            s.readiness=min(1.,s.readiness+.030*dt)
        elif behavior=='sleep':
            s.fatigue=max(0.,s.fatigue-.24*dt)
            s.readiness=min(1.,s.readiness+.24*dt)
            s.sleep_pressure=max(0.,s.sleep_pressure-.30*dt)
        else:
            s.sleep_pressure=min(1.,s.sleep_pressure+.07*dt)
            s.readiness=max(.05,s.readiness-.016*dt)
        if behavior in ('sleep','rest') and a.condition<1. and self._fuel(a)>.0004:
            repair=.00010*dt
            if self._consume_short(a,repair,'repair')>=repair-1e-9:
                a.condition=min(1.,a.condition+.0025*dt)
        if s.sleep_pressure>.82:s.readiness=max(.05,s.readiness-.025*dt)

    def _move_with_duration(self,a,action,t):
        s=self._state(a)
        # Elapsed physical time of actual movement -- never actor-owned credits.
        next_ready=getattr(s,'motion_ready_at',-1.)
        if t+1e-9<next_ready:return False
        moved=self._migrate(a,action)
        if moved:
            speed=max(.6,3.3/(1.+self._bodymass(a)**.3))
            s.motion_ready_at=t+1./speed
            self.physiology_metrics['resolved_motion']+=1
        return moved

    def _flee(self,a):
        """A small predator can escape a larger predator by paying real travel work."""
        if not self.eco_flags.spatial:return False
        here=self._pos(a)
        threats=[p for p in self.actors.values() if p.alive and
                 p.habitat==a.habitat and a.species in PREY.get(p.species,())]
        if not threats:return False
        neighbors=self._neighbors(here)
        if not neighbors:return False
        def margin(cell):
            return min(abs(cell[1]-self._pos(p)[1])+abs(cell[2]-self._pos(p)[2])
                       for p in threats)
        best=max(neighbors,key=lambda cell:(margin(cell),-cell[1],-cell[2]))
        if margin(best)<margin(here):return False
        if not self._work(a,'avoid_large_predator',effort=.65):return False
        self.positions[a.id]=best
        a.hidden=False
        self.physiology_metrics['predator_evasion_steps']+=1
        return True

    def _hunt(self,a):
        """Search/pursuit may bring a local predator within a hunting cell."""
        if a.species in PREY and self.eco_flags.spatial:
            visible=[x for x in self.actors.values() if x.alive and
                     x.species in PREY[a.species] and x.habitat==a.habitat]
            if visible:
                here=self._pos(a)
                nearest=min(visible,key=lambda p:(abs(self._pos(p)[1]-here[1])+
                              abs(self._pos(p)[2]-here[2]),p.id))
                distance=abs(self._pos(nearest)[1]-here[1])+abs(self._pos(nearest)[2]-here[2])
                if distance>1:
                    neighboring=self._neighbors(here)
                    choices=sorted(neighboring,key=lambda loc:(abs(loc[1]-self._pos(nearest)[1])+
                                                               abs(loc[2]-self._pos(nearest)[2]),loc))
                    if choices and self._work(a,'prey_tracking',effort=.32):
                        self.positions[a.id]=choices[0]
                        self.physiology_metrics['funded_tracking_steps']+=1
                        now=self._pos(a)
                        if abs(now[1]-self._pos(nearest)[1])+abs(now[2]-self._pos(nearest)[2])<=1:
                            return super()._hunt(a)
                    return False
        return super()._hunt(a)

    def _birth(self,mom):
        # Maternal food energy accumulated during digestion becomes offspring
        # tissue energy, not a second copy of the mother's physical reserve.
        existing=set(self.actors)
        n=super()._birth(mom)
        if n:
            offspring=[x for uid,x in self.actors.items() if uid not in existing
                       and x.parent==mom.id]
            maternal_energy=self.physical.maternal_energy(mom)
            for child in offspring:
                target=self.book.mass[self.physical.live(child)]*ANIMAL_TISSUE_ENERGY_DENSITY
                q=min(target,self.book.energy[maternal_energy])
                if q>1e-12:self.book.move(energy=[(maternal_energy,self.physical.tissue(child),q)])
                self._state(child)
            self.physiology_metrics['funded_newborns']+=len(offspring)
        return n

    def _decay(self):
        # Native and bridge have explicit carcass/detritus mass transfers.
        # Keep historical decay; reconcile plant lots at the next producer tick.
        super()._decay()

    def _fatal_condition(self,a,st):
        """Historical failure rule; overridable by a physiology service."""
        return a.condition<=.06 or st.starvation_debt>=.98

    def step(self,tick):
        """Four overlapping process resolutions per world day.

        Substeps are numerical integration samples, not a number of action
        tokens. Decisions may recur as conditions change; distinct physical
        activities are bounded by elapsed physical duration and energy.
        """
        if tick!=self.day+1:raise AssertionError('physiology clock mismatch')
        self.day=tick
        if self.tree.state not in ('active','germinating'):
            for a in list(self.actors.values()):
                if a.alive:self._death(a,'world_tree_collapse')
            self.book.audit();self._check_registry();return
        self.sync_positions()
        self.lots.balance_all()
        if self.eco_flags.spatial:self._refresh_quota()
        actors=tuple(self.actors.values())
        for a in actors:
            if a.alive:a.age+=1
        dt=1.0/self.substeps
        self._current_dt=dt
        with _temporary_diet_registry():
            for sub in range(self.substeps):
                self._substep_index = sub  # resolved world-clock fraction, NOT time currency
                elapsed=(tick-1)+sub*dt
                # Synthetic registry order is not ecological action priority.
                # Only the Cycle146 treatment randomizes activation order;
                # default Core145 replay and all-off controls remain unchanged.
                active_order=list(actors)
                if getattr(self,'fair_trophic_scheduler',False):
                    self.rng.shuffle(active_order)
                for a in active_order:
                    if not a.alive:continue
                    self._metabolize(a,dt)
                    action,hunger,danger=self._choose(a)
                    if action=='flee':
                        self._flee(a)
                    elif action=='hide':
                        a.hidden = self.rng.random() < min(.95,COVER[a.habitat]*(.6+.4*a.avoid_skill))
                    elif action not in ('rest','sleep','care','stay_with_caregiver'):
                        a.hidden=False
                        self._move_with_duration(a,action,elapsed)
                    if a.species in PREY:
                        if action in ('feed','search'):self._hunt(a)
                    elif a.species=='carrion_bird':
                        if action in ('feed','search'):self._feed_scavenger(a)
                    elif a.stage!='dependent' and action in ('feed','search'):
                        self._feed_herbivore(a)
                    if a.stage in ('adult','elder') and (action=='care' or sub==self.substeps-1):
                        self._care(a,'physical_caregiver')
                    self._finish_behavior(a,action,dt)
                    st=self._state(a)
                    if (self._fatal_condition(a,st) or
                        a.age>=PROFILES[a.species].max_age):
                        self._death(a,'age' if a.age>=PROFILES[a.species].max_age else 'physiological_failure')
            for a in actors:
                if a.alive and self.rng.random()<PROFILES[a.species].hazard*(3 if a.stage=='elder' else 1):
                    self._death(a,'baseline_mortality')
            self._reproduce();self._decay()
            for a in tuple(self.actors.values()):
                if not a.alive:continue
                self._state(a)
                if a.species==ANTS:
                    self._ant_brood(a);self._ant_daughter_colony(a)
                elif a.species in MEGA:self._megaherbivore_turnover(a)
        self.lots.balance_all()
        self.sync_positions();self.book.audit();self._check_registry()

    def five_phase_report(self):
        pop={p:sum(x.alive and x.species==p for x in self.actors.values())
             for p in PROFILES}
        return {'species':pop,'physiology':self.physiology_report(),
                'lot_metrics':dict(self.lots.metrics),
                'edible_producer_energy':sum(self.book.energy[self.lots.plant(h).energy_account]
                                              for h in self.tree.habitats),
                'world_sun':sum(self.book.energy[self.tree.acct('sun',h)] for h in self.tree.habitats)}


class UnifiedFivePhase142(UnifiedCoreV2):
    """Single Book, clock and active bridge; native scheduler remains distinct."""
    def __init__(self,*args, founder_world_support=True, substeps=N_SUBSTEPS,**kwargs):
        super().__init__(*args,founder_world_support=founder_world_support,**kwargs)
        if type(self.bridge) is not PhysiologyBridgeV2:
            raise TypeError('expected single Core v2 bridge')
        self.bridge.__class__=FivePhaseBridge142
        self.bridge.activate_five_phases(substeps=substeps)
        if self.world_support is not None:
            self.world_support.__class__=MechanismAwareWorldFunding142
        self._check()

    def report(self):
        r=super().report()
        r['five_phase_142']={'status':'experimental_candidate_not_promoted',
           'single_book':self.host.book is self.bridge.book is self.bridge.tree.book,
           'days':self.days,'native_population':self.bridge.tree.population,
           **self.bridge.five_phase_report()}
        return r
