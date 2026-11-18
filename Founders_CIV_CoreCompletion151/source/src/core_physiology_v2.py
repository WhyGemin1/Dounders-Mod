"""Founders-CIV Core V2 integration candidate (NOT automatically promoted canonical).

One Book and one World Tree, 100 Founders, the existing native residents and
bridge animal scheduler. The bridge's old daily physiology scheduler is replaced,
not composed with another energy override. The 13 guilds share ONE new physical
physiology while keeping their real Book inventories and stage-specific ecology.

Time: world clock in days, not consumable time credits. A daily resolution is an
approximation of rates and ordered events, not a 24-action wallet. Physiology
rates are exploratory parameters, not calibrated empirical values.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from contextlib import contextmanager
from math import isfinite

from trophic_guilds_cycle138 import (
    GuildBridge138, UnifiedTrophicGuild138, _temporary_diet_registry,
    GUILD_PREDATORS, ALLOWED_HABITATS, MEGA, ANTS, MIN_QUEEN_MASS,
)
from species_life_02115 import PROFILES, COVER, YEAR, NEEDS
from habitat_bridge import PREY
from digestion_02120 import PLANT_DIGESTIBILITY, CARRION_DIGESTIBILITY
from founder_world_energy_141 import FounderWorldSupport141

# These are documented simulation coefficients, not measured SI constants.
# The engine's historical mass and energy ledger units are synthetic.
MAX_FATIGUE = 1.0
DIGESTION_FRACTION = 0.42  # fraction of gut contents processed per simulated day
MOBILIZATION_FRACTION = 0.55
REPAIR_COST = .00010

@dataclass
class FunctionalState:
    fatigue:float = 0.08
    readiness:float = 0.85
    sleep_pressure:float = 0.12
    starvation_debt:float = 0.0
    last_behavior:str = 'rest'
    experience:float = 0.0
    gut_quality_weight:float = 0.0
    gut_energy_weight:float = 0.0
    # energy stocks live ONLY in Book; these variables do not hold energy.

class PhysiologyBridgeV2(GuildBridge138):
    """Single active bridge physiology replaces preaction metabolic penalties.

    The guild/eco/family/World Tree modules retain environment and policy, but
    energy processing, feeding, predation and action work have only this live
    physiological implementation; no legacy parent step or feed/hunt calls.
    """
    def activate_physiology(self):
        self.functional={a.id:FunctionalState() for a in self.actors.values()}
        self.physiology_metrics=Counter()
        # Migration moves existing reserves to the new, independently backed
        # *short term* substrate account without changing the total Book.
        for a in self.actors.values():
            reserve=self.physical.reserve(a)
            short=self._short(a)
            transfer=min(.004,max(0.,self.book.energy[reserve]*.20))
            if transfer>0:self.book.move(energy=[(reserve,short,transfer)])
        assert self.book.audit()['rejections']==0

    def _state(self,a):
        if a.id not in self.functional:self.functional[a.id]=FunctionalState()
        return self.functional[a.id]

    @staticmethod
    def _short(a):return f'substrate:{a.id}'
    @staticmethod
    def _gut_energy(a):return f'gut_energy:{a.id}'

    def _fuel(self,a):
        return self.book.energy[self._short(a)]+self.book.energy[self.physical.reserve(a)]

    def _bodymass(self,a):return max(.003,self.book.mass[self.physical.live(a)])

    def _maintenance_demand(self,a):
        p=PROFILES[a.species]
        body=self._bodymass(a)
        # Allometric shape in historical synthetic units; homeotherm/caste/
        # temperature biology must be calibrated in future empirical work.
        basal=.00022*(body/.05)**.7*(p.metabolism/.085)**.3
        if a.species==ANTS:basal*=.35  # one colony actor, pooled workers
        return basal

    def _mobilize(self,a,wanted):
        """Book-funded mobilization, finite fraction per day."""
        short=self._short(a); long=self.physical.reserve(a)
        cap=.005 + .002*(self._bodymass(a)/.05)**.5
        take=min(max(0.,wanted),cap,self.book.energy[long]*MOBILIZATION_FRACTION)
        if take>1e-12:
            self.book.move(energy=[(long,short,take)])
            self.physiology_metrics['mobilizations']+=1
        return take

    def _consume_short(self,a,requested,category):
        short=self._short(a)
        available=self.book.energy[short]
        if available+1e-12<requested:self._mobilize(a,requested-available)
        realized=min(max(0.,requested),self.book.energy[short])
        if realized>1e-12:self.book.move(energy=[(short,'environment:heat',realized)])
        self.physiology_metrics[f'{category}_energy']+=realized
        return realized

    def _digest(self,a):
        """Move existing gut mass/energy to tissue, maternal stores, waste, fuel.

        Digestion happens regardless of activity/sleep. Food entered gut on a
        previous action; no instant meal->usable-fuel path. Book energy is
        partitioned proportionally to digested gut mass.
        """
        b=self.book; ph=self.physical; s=self._state(a)
        gut=ph.gut(a); gm=b.mass[gut]
        if gm<=1e-12:return
        q=gm*DIGESTION_FRACTION
        ge=self._gut_energy(a); ge_available=b.energy[ge]
        e=ge_available*(q/max(gm,1e-12))
        p=PROFILES[a.species]
        target=p.adult_mass()*(.35+.65*min(1.,a.age/max(1,p.maturity)))
        grow=(min(q*.14,max(0.,target-b.mass[ph.live(a)])) if a.age<p.maturity else 0.)
        maternal=(min(q*.15,max(0.,p.maternal_cap()-b.mass[ph.maternal(a)]))
                  if a.sex=='F' and a.stage=='adult' else 0.)
        waste=max(0.,q-grow-maternal)
        legs=[]
        for dest,x in ((ph.live(a),grow),(ph.maternal(a),maternal),(ph.detritus(a),waste)):
            if x>1e-12:legs.append((gut,dest,x))
        if legs:ph.convert(legs)
        assimilation=min(1.,max(0.,s.gut_quality_weight/max(s.gut_energy_weight,1e-12)))
        if e>1e-12:
            useful=e*assimilation
            tissue=useful*grow/max(q,1e-12)
            maternal_energy=useful*maternal/max(q,1e-12)
            short=useful-tissue-maternal_energy
            legs=[(ge,k,v) for k,v in ((ph.tissue(a),tissue),
                  (ph.maternal_energy(a),maternal_energy),
                  (self._short(a),short),('environment:heat',e-useful)) if v>1e-12]
            if legs:b.move(energy=legs)
            self.physiology_metrics['absorbed_energy']+=useful
            self.physiology_metrics['digestion_heat']+=e-useful
        s.gut_quality_weight=max(0.,s.gut_quality_weight-e*assimilation) if e>0 else s.gut_quality_weight
        s.gut_energy_weight=max(0.,s.gut_energy_weight-e)
        self.physiology_metrics['digested_mass']+=q

    def _metabolize(self,a):
        """Process digestion and basal metabolism independent of previous action.

        This uses no last-action tax. End-of-day physical behavior is recorded
        elsewhere only when the action has actually resolved.
        """
        if not a.alive:return
        s=self._state(a)
        self._digest(a)
        demand=self._maintenance_demand(a)
        realized=self._consume_short(a,demand,'maintenance')
        if realized+.0000001 < demand:
            deficit=(demand-realized)/max(demand,.000001)
            s.starvation_debt+=.07*deficit
            a.condition=max(0.,a.condition-.018*deficit)
        else:
            s.starvation_debt=max(0.,s.starvation_debt-.006)
        self.physiology_metrics['metabolic_steps']+=1

    def _work(self,a,activity,effort=1.0):
        """Pay only when a physical effort resolves, proportional to body size.

        Returning False causes the attempted movement or strike not to resolve.
        No energy debit is attached to the decision itself.
        """
        s=self._state(a);p=PROFILES[a.species]
        scale=(self._bodymass(a)/.05)**.64
        learned=1.0+min(.5,s.experience*.20)
        readiness=max(.20,s.readiness)
        efficiency=max(.35,(1.-.34*s.fatigue)*readiness*learned)
        demand=.000055*scale*effort/max(efficiency,.1)
        short=self.book.energy[self._short(a)]
        long=self.book.energy[self.physical.reserve(a)]
        mobilizable=min(long*MOBILIZATION_FRACTION, .005+.002*(self._bodymass(a)/.05)**.5)
        if short+mobilizable+1e-12<demand:
            self.physiology_metrics['work_unfunded']+=1
            return False
        paid=self._consume_short(a,demand,'resolved_work')
        if paid+1e-11<demand:
            self.physiology_metrics['work_power_limited']+=1
            return False
        s.fatigue=min(MAX_FATIGUE,s.fatigue+.018*effort/(readiness*learned))
        s.experience=min(2.,s.experience+.0006)
        self.physiology_metrics[f'activity:{activity}']+=1
        return True

    def _refresh_quota(self):
        # The older spatial arm makes plant/carrion local. Detritus is an
        # additional real resource for ant colonies, never a new Book stock.
        super()._refresh_quota()
        if not self.eco_flags.spatial:return
        z=self.grid_size
        for h in self.tree.habitats:
            source=self.tree.acct('detritus',h)
            if (source,h,0,0) in self._cell_quota:continue
            available=self.book.mass[source]*.42
            weights={(x,y):self._cell_weight(h,x,y,'detritus')
                     for x in range(z) for y in range(z)}
            den=sum(weights.values())
            for (x,y),w in weights.items():
                self._cell_quota[(source,h,x,y)]=available*w/max(den,1e-12)

    def _feed_stock(self,a,source,kind):
        """Physical food lots: external biomass+embodied energy to gut only."""
        if not a.alive:return False
        ph=self.physical;b=self.book;p=PROFILES[a.species]
        fraction=(.65+.35*min(1.,a.age/max(1,p.maturity))) if a.stage in ('juvenile','dependent') else 1.
        q=min(p.intake*.012*fraction,self._local_access(a,source))
        carrion=(source==self.carrion(a.habitat))
        if not carrion:q=min(q,max(0.,b.energy[ph.chem(a)]/.80))
        if q<.0004:return False
        source_mass=b.mass[source]
        ph.convert([(source,ph.gut(a),q)])
        origin=ph.carrion_energy(a.habitat) if carrion else ph.chem(a)
        intake=(min(b.energy[origin],b.energy[origin]*q/max(source_mass,1e-12))
                if carrion else min(b.energy[origin],q*.80))
        if intake>0:b.move(energy=[(origin,self._gut_energy(a),intake)])
        s=self._state(a)
        quality=(CARRION_DIGESTIBILITY if carrion else PLANT_DIGESTIBILITY)
        if kind in ('ant_detritus','insect_worker'):quality=min(quality,.35)
        s.gut_quality_weight+=intake*quality
        s.gut_energy_weight+=intake
        if self.eco_flags.spatial:
            key=(source,*self._pos(a))
            if key in self._cell_quota:self._cell_quota[key]=max(0.,self._cell_quota[key]-q)
        self.physiology_metrics['ingested_mass']+=q
        self.physiology_metrics['ingested_energy']+=intake
        self._log('feeding',actor=a.id,habitat=a.habitat,food_source=kind,mass=q,
                  into_gut_energy=intake,absorbed_immediately=0.0)
        return True

    def _choose(self,a):
        action,hunger,danger=super().evaluate_needs(a)
        s=self._state(a)
        # Dependent juveniles also need actual sleep. Caregiver proximity is
        # not a substitute for sleep and must not trap their pressure at 1.
        # Preserve immediate danger response and caregiver attachment.
        if a.stage=='dependent':
            # The underlying needs policy owns immediate danger response.
            # Caregiver attachment must not suppress an actual escape/defense
            # decision; nor may fatigue force sleep in danger.
            if danger:
                # Never let a passive caregiver/rest choice override an
                # immediate threat. Preserve an active escape/defense policy.
                if action in ('rest','sleep','stay_with_caregiver','care','feed','search','mate'):
                    return 'hide',hunger,danger
                return action,hunger,danger
            if s.sleep_pressure>.82 or s.fatigue>.76:
                return 'sleep',hunger,danger
            return 'stay_with_caregiver',hunger,danger
        if not danger and (s.fatigue>.76 or s.readiness<.28 or s.sleep_pressure>.82):
            return 'sleep',hunger,danger
        if not danger and (s.fatigue>.52 or s.readiness<.43):
            return 'rest',hunger,danger
        # Short-term and reserve capacity inform feeding, but the old
        # policy remains a documented hybrid until fully recalibrated.
        # Rest is driven by fatigue/readiness above, never by merely having
        # food in the gut and fuel in reserve. The old last-rest condition
        # could trap a nourished actor in perpetual rest even after recovery.
        return action,hunger,danger

    def _finish_behavior(self,a,behavior):
        s=self._state(a);s.last_behavior=behavior
        if behavior in ('rest','stay_with_caregiver'):
            s.fatigue=max(0.,s.fatigue-.12)
            s.readiness=min(1.,s.readiness+.025)
            # Quiet wakefulness conserves fuel and eases exertion, but it is
            # not sleep: sleep pressure still accumulates. Dependent animals
            # can remain with caregivers without acquiring free sleep.
            s.sleep_pressure=min(1.,s.sleep_pressure+
                                 (.020 if behavior=='stay_with_caregiver' else .012))
        elif behavior=='sleep':
            s.fatigue=max(0.,s.fatigue-.23)
            s.readiness=min(1.,s.readiness+.22)
            s.sleep_pressure=max(0.,s.sleep_pressure-.29)
        else:
            s.sleep_pressure=min(1.,s.sleep_pressure+.034)
            s.readiness=max(.05,s.readiness-.012)
        # Injury/tissue repair takes real substrate; no Book minting.
        if behavior in ('sleep','rest') and a.condition<1. and self._fuel(a)>REPAIR_COST*4:
            if self._consume_short(a,REPAIR_COST,'repair')>=REPAIR_COST-.00000001:
                a.condition=min(1.,a.condition+.0025)
        if s.sleep_pressure>.82:s.readiness=max(.05,s.readiness-.03)

    def _migrate(self,a,decision=None):
        if a.species==ANTS or a.stage=='dependent' or decision in ('rest','sleep','care','mate','stay_with_caregiver','hide','defend'):
            return False
        here=a.habitat;neighbors=[h for h in self.tree.habitats[here].neighbors]
        if a.species in MEGA:
            if self.day%9:return False
            neighbors=[h for h in neighbors if h in ALLOWED_HABITATS[a.species]]
        target=None
        if neighbors:
            if a.species in PREY:
                found=[h for h in neighbors if any(x.alive and x.habitat==h and x.species in PREY[a.species] for x in self.actors.values())]
                if found and self.rng.random()<.55:target=self.rng.choice(found)
                elif self.day%7==0 and self.rng.random()<.30:target=self.rng.choice(neighbors)
            elif self.day%3==0 and self.book.mass[self.physical.plant(a)]<.22:
                target=max(neighbors,key=lambda h:self.book.mass[self.tree.acct('plant',h)])
        if target is not None and target!=here:
            if not self._work(a,'habitat_movement',effort=2.4):return False
            a.habitat=target;self.sync_positions()
            self._log('migration',actor=a.id,from_habitat=here,to_habitat=target,
                      reason='local_cues',cost_model='current_resolved_work')
            self.physiology_metrics['habitat_migrations']+=1
            return True
        if self.eco_flags.spatial:
            self._refresh_quota()
            old=self._pos(a);near=self._neighbors(old)
            if not near:return False
            if a.species in PREY:
                cells={self._pos(x) for x in self.actors.values() if x.alive and x.species in PREY[a.species] and x.habitat==a.habitat}
                score=lambda cell:int(cell in cells)
            else:
                source=(self.carrion(a.habitat) if a.species=='carrion_bird' else self.physical.plant(a))
                score=lambda cell:self._cell_quota.get((source,*cell),0.)
            best=max(near,key=lambda cell:(score(cell),-cell[1],-cell[2]))
            if not self._work(a,'cell_movement',effort=.42):return False
            self.positions[a.id]=best
            self.physiology_metrics['cell_moves']+=1
            for child in self.actors.values():
                if child.alive and child.stage=='dependent' and a.id in child.caregiver_ids and child.habitat==a.habitat:
                    self.positions[child.id]=best
            return True
        return False

    def _hunt(self,a):
        """Encounter/strike/kill are resolved here; no previous-action tax.

        Ingested flesh and embodied tissue energy enter gut, not usable reserve.
        The victim's short-term energy and gut food have explicit corpse fates.
        """
        if a.species=='insectivore_shrew':
            if self._ant_worker_take(a):return True
        if a.species not in PREY:return self._optional_scavenge(a) if a.species=='insectivore_shrew' else False
        prey=[x for x in self.actors.values() if x.alive and x.species in PREY[a.species]
              and x.id!=a.id and x.habitat==a.habitat]
        if self.eco_flags.spatial:
            here=self._pos(a)
            prey=[x for x in prey if sum(abs(here[i]-self._pos(x)[i]) for i in (1,2))<=1]
        if not prey:return self._optional_scavenge(a) if a.species in ('red_fox','golden_jackal') else False
        cover=COVER[a.habitat]
        detected=[x for x in prey if self.rng.random()<max(.05,.75-cover*.38-(.35 if x.hidden else 0))]
        if not detected:return False
        victim=self.rng.choice(detected)
        if not self._work(a,'strike',effort=1.8):return False
        self._log('hunt_attempt',actor=a.id,prey=victim.id,habitat=a.habitat)
        s=self._state(a)
        chance=max(.02,min(.74,.18+.24*a.hunt_skill+.16*(victim.stage=='dependent')
              -.21*victim.avoid_skill-.08*cover-(.14 if victim.hidden else 0)))
        chance*=max(.25,(1.-.36*s.fatigue)*s.readiness)
        if self.rng.random()>=chance:
            victim.avoid_skill=min(1.,victim.avoid_skill+.0035)
            self._log('escape',actor=victim.id,predator=a.id,habitat=victim.habitat)
            return False
        b=self.book; ph=self.physical
        body=b.mass[ph.live(victim)]; eaten=body*.30
        if body>1e-12:
            ph.convert([(ph.live(victim),ph.gut(a),eaten),
                        (ph.live(victim),self.carrion(a.habitat),body-eaten)])
        carrion_energy=ph.carrion_energy(a.habitat)
        tissue=ph.tissue(victim); t=b.energy[tissue]
        if t>1e-12:b.move(energy=[(tissue,self._gut_energy(a),t*.30),
                                  (tissue,carrion_energy,t*.70)])
        s.gut_quality_weight+=t*.30*CARRION_DIGESTIBILITY
        s.gut_energy_weight+=t*.30
        for key in (ph.maternal(victim),ph.gut(victim)):
            x=b.mass[key]
            if x>1e-12:ph.convert([(key,self.carrion(a.habitat),x)])
        for key in (ph.maternal_energy(victim),self._gut_energy(victim),
                    ph.reserve(victim),self._short(victim)):
            x=b.energy[key]
            if x>1e-12:b.move(energy=[(key,carrion_energy,x)])
        victim.alive=False;victim.pregnant_until=None;victim.pregnancy_father=None
        for other in self.actors.values():other.caregiver_ids.discard(victim.id)
        a.hunt_skill=min(1.,a.hunt_skill+.0035)
        self._log('death',actor=victim.id,species=victim.species,cause='predation',habitat=victim.habitat)
        self._log('predation',predator=a.id,prey=victim.id,habitat=a.habitat,prey_mass=body)
        self.physiology_metrics['kills']+=1
        return True

    def _ant_worker_take(self,a):
        colonies=[x for x in self.actors.values() if x.alive and x.species==ANTS
                  and x.habitat==a.habitat and
                  (not self.eco_flags.spatial or
                   sum(abs(self._pos(a)[i]-self._pos(x)[i]) for i in (1,2))<=1)]
        if not colonies:return False
        colony=max(colonies,key=lambda x:self.book.mass[self.physical.live(x)])
        available=self.book.mass[self.physical.live(colony)]-MIN_QUEEN_MASS
        q=min(.0015,max(0.,available))
        if q<.0004 or not self._work(a,'insect_hunt',effort=.75):return False
        b=self.book;ph=self.physical
        cm=b.mass[ph.live(colony)];t=ph.tissue(colony)
        e=min(b.energy[t],b.energy[t]*q/max(cm,1e-12))
        ph.convert([(ph.live(colony),ph.gut(a),q)])
        if e>1e-12:b.move(energy=[(t,self._gut_energy(a),e)])
        s=self._state(a);s.gut_quality_weight+=e*.65;s.gut_energy_weight+=e
        self.physiology_metrics['ant_worker_meals']+=1
        self._log('ant_worker_foraging',predator=a.id,colony=colony.id,mass=q)
        return True

    def _ant_brood(self,a):
        """Worker biomass funded by detritus mass and previously assimilated fuel."""
        if self.day%6:return
        b=self.book;ph=self.physical
        if b.mass[ph.live(a)]>=.12:return
        det=self.tree.acct('detritus',a.habitat)
        q=min(.0020,max(0.,.12-b.mass[ph.live(a)])/.35,b.mass[det])
        cost=q*.40
        if q<.0001 or b.energy[self._short(a)]<cost:return
        ph.convert([(det,ph.live(a),q*.35),
                    (det,self.tree.acct('soil',a.habitat),q*.65)])
        b.move(energy=[(self._short(a),ph.tissue(a),cost*.45),
                       (self._short(a),'environment:heat',cost*.55)])
        self.guild_metrics['new_worker_biomass']+=q*.35
        self.guild_metrics['ant_nutrient_mineralization']+=q*.65

    def _care(self,a,episode='primary'):
        if a.stage not in ('adult','elder'):return False
        children=[x for x in self.actors.values() if x.alive and x.stage=='dependent'
                  and a.id in x.caregiver_ids and x.habitat==a.habitat]
        done=False
        for child in children:
            if self.eco_flags.spatial and self._pos(child)!=self._pos(a):continue
            if self._child_fed_day.get(child.id)==self.day:continue
            source=(self.carrion(a.habitat) if a.species in PREY else self.physical.plant(a))
            if source==self.physical.plant(a) and self.book.mass[source]<.04:continue
            if self._local_access(a,source)<.0004:continue
            if not self._work(a,'caregiving',effort=.35):continue
            if self._feed_stock(child,source,'parental_provision'):
                self._child_fed_day[child.id]=self.day
                self.physiology_metrics['provisioned_children']+=1
                done=True
        return done

    def _death(self,a,cause):
        if not a.alive:return
        dest=(self.physical.carrion_energy(a.habitat) if self.tree.state in ('active','germinating')
              else 'environment:heat')
        for account in (self._short(a),self._gut_energy(a)):
            x=self.book.energy[account]
            if x>1e-12:self.book.move(energy=[(account,dest,x)])
        return super()._death(a,cause)

    def _check_registry(self):
        super()._check_registry()
        if not hasattr(self,'functional'):return
        for a in self.actors.values():
            s=self._state(a)
            for v in (s.fatigue,s.readiness,s.sleep_pressure,s.starvation_debt):
                if not isfinite(v):raise AssertionError('nonfinite physiology')
            assert 0<=s.fatigue<=1 and 0<=s.readiness<=1 and 0<=s.sleep_pressure<=1
            if not a.alive:
                assert self.book.energy[self._short(a)]<1e-8
                assert self.book.energy[self._gut_energy(a)]<1e-8

    def step(self,tick):
        """Replacement life-history step, not super().step legacy toll chain."""
        if tick!=self.day+1:raise AssertionError('physiology clock mismatch')
        self.day=tick
        if self.tree.state not in ('active','germinating'):
            for a in list(self.actors.values()):
                if a.alive:self._death(a,'world_tree_collapse')
            for habitat in self.tree.habitats:
                q=self.book.mass[self.carrion(habitat)]
                if q>0:self.physical.convert([(self.carrion(habitat),f'remnant:tree:{self.tree.id}:{habitat}',q)])
                e=self.book.energy[self.physical.carrion_energy(habitat)]
                if e>0:self.book.move(energy=[(self.physical.carrion_energy(habitat),'environment:heat',e)])
            self.book.audit();self._check_registry();return
        self.sync_positions()
        if self.eco_flags.spatial:self._refresh_quota()
        with _temporary_diet_registry():
            for a in list(self.actors.values()):
                if not a.alive:continue
                self._state(a)
                a.age+=1
                self._metabolize(a)
                action,hunger,danger=self._choose(a)
                self._migrate(a,action)
                if a.species in PREY:
                    if action in ('feed','search'):self._hunt(a)
                elif a.species=='carrion_bird':
                    if action in ('feed','search'):self._feed_scavenger(a)
                elif a.stage!='dependent' and action not in ('rest','sleep'):
                    if action=='feed' or (action=='search' and hunger>.55):
                        self._feed_herbivore(a)
                if a.stage in ('adult','elder'):
                    if action=='care' and not danger:
                        self._care(a,'primary')
                    elif not danger and action not in ('hide','escape','defend','rest','sleep'):
                        if self.rng.random()<.40:self._care(a,'secondary')
                self._finish_behavior(a,action)
                st=self._state(a)
                if (a.condition<=.06 or st.starvation_debt>=.98 or a.age>=PROFILES[a.species].max_age):
                    self._death(a,'age' if a.age>=PROFILES[a.species].max_age else 'physiological_failure')
                elif self.rng.random()<PROFILES[a.species].hazard*(3 if a.stage=='elder' else 1):
                    self._death(a,'baseline_mortality')
            self._reproduce();self._decay()
            for a in tuple(self.actors.values()):
                if not a.alive:continue
                self._state(a)
                if a.species==ANTS:
                    self._ant_brood(a);self._ant_daughter_colony(a)
                elif a.species in MEGA:self._megaherbivore_turnover(a)
        self.sync_positions();self.book.audit();self._check_registry()

    def physiology_report(self):
        alive=[a for a in self.actors.values() if a.alive]
        return {
          'animals_alive':len(alive),'distinct_species':len({a.species for a in alive}),
          'total_gut_mass':sum(self.book.mass[self.physical.gut(a)] for a in alive),
          'total_gut_energy':sum(self.book.energy[self._gut_energy(a)] for a in alive),
          'short_term_energy':sum(self.book.energy[self._short(a)] for a in alive),
          'long_term_energy':sum(self.book.energy[self.physical.reserve(a)] for a in alive),
          'mean_fatigue':sum(self._state(a).fatigue for a in alive)/max(1,len(alive)),
          'mean_readiness':sum(self._state(a).readiness for a in alive)/max(1,len(alive)),
          'metrics':dict(self.physiology_metrics)}

class UnifiedCoreV2(UnifiedTrophicGuild138):
    """Candidate single-engine composition of energy/species/ecology."""
    def __init__(self,seed=9711,*,expanded_food_web=True,metabolism=True,spatial=True,
                 juvenile=True,founder_world_support=False,**kwargs):
        super().__init__(seed=seed,expanded_food_web=expanded_food_web,
                         metabolism=metabolism,spatial=spatial,juvenile=juvenile,**kwargs)
        # A guild-free v2 uses the exact same physiological process by
        # default; this release candidate currently requires expanded guilds.
        if type(self.bridge) is not GuildBridge138:
            raise TypeError('CoreV2 requires the actual guild bridge')
        self.bridge.__class__=PhysiologyBridgeV2
        self.bridge.activate_physiology()
        assert self.host.book is self.bridge.book is self.bridge.tree.book
        self.world_support=FounderWorldSupport141(self) if founder_world_support else None
        if self.world_support:self.world_support.activate()
        self._check()

    def step(self):
        # Founder endowments power producer work before the next World Tree tick.
        # There is no energy grant to organisms or time currency.
        if self.world_support:self.world_support.maintain()
        return super().step()

    def report(self):
        output=super().report()
        output['core_v2']={'status':'integration_candidate_not_promoted',
                           'one_book':self.host.book is self.bridge.book,
                           'elapsed_world_days':self.days,
                           'physiology':self.bridge.physiology_report()}
        output['world_support_141']=self.world_support.report() if self.world_support else None
        return output
