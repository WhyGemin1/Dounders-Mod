"""Cycle146: one-Book trophic ecological expansion on Core145 G2-repaired engine.

Experiment, not canonical. Single World, 100 Founders, native/bridge schedulers.
Time is physical elapsed time; no feeding or action credits. All transferred
biomass and chemical energy comes from recorded Book accounts.
"""
from __future__ import annotations
from collections import Counter
from math import isfinite
from core_completion_145 import (UnifiedCoreCompletion145, CoreCompletionBridge145,
                                  CoreCompletionWorld145)
from core_completion_144 import EcologicalProduction144
from five_phase_core_142 import EdibleLot, ANIMAL_TISSUE_ENERGY_DENSITY
from core_physiology_v2 import PREY, COVER, PROFILES, ANTS, CARRION_DIGESTIBILITY
from trophic_roles_146 import CARNIVORE_ROLES, HABITAT_REFUGE, PREY_SHELTER, PREY_PREFERENCE, PLANT_EATER_ROLES


class TrophicInventory146(EcologicalProduction144):
    def carrion(self, habitat):
        """Carrion uses its ACTUAL paired Book caloric density, not nominal .45.

        Somatic growth can yield variable embodied tissue-energy per mass and
        carcasses hold stomach contents and fuel reserves. A fixed .45 density
        made genuine carrion inaccessible despite recorded Book energy.
        """
        b=self.bridge;mass=b.book.mass[b.carrion(habitat)]
        energy=b.book.energy[b.physical.carrion_energy(habitat)]
        density=min(1.5,energy/max(mass,1e-12)) if mass>1e-12 else ANIMAL_TISSUE_ENERGY_DENSITY
        return EdibleLot(b.carrion(habitat),b.physical.carrion_energy(habitat),
                         habitat,'animal_carrion',max(1e-9,density))


class CoreCompletionBridge146(CoreCompletionBridge145):
    def activate_trophic(self,*,diet=True,hunting=True,provisioning=True):
        self.trophic_flags={'diet':bool(diet),'hunting':bool(hunting),
                           'provisioning':bool(provisioning)}
        self.trophic_metrics=Counter()
        self.fair_trophic_scheduler=bool(hunting)

    def _consume_short(self,a,requested,category):
        paid=super()._consume_short(a,requested,category)
        if category!='maintenance' or not self.trophic_flags['diet'] or not a.alive:
            return paid
        deficit=max(0.,requested-paid)
        if deficit<=1e-12:return paid
        b=self.book;ph=self.physical
        live=ph.live(a);tissue=ph.tissue(a)
        body=b.mass[live]; embodied=b.energy[tissue]
        if body<=1e-10 or embodied<=1e-10:return paid
        profile=PROFILES[a.species]
        # Catabolism is constrained by remaining structural tissue, not a
        # universal fallback energy wallet. Carnivores can mobilize reserves
        # more gradually; all other animals retain ordinary fasting capacity.
        minimum=max(profile.newborn_mass()*.80,profile.adult_mass()*.35)
        surplus_mass=max(0.,body-minimum)
        if surplus_mass<=1e-9:return paid
        density=embodied/body
        efficiency=.82 if self._diet_role(a) else .76
        # This Book models tissue->detritus as a material-state transformation
        # requiring a WORK toll, funded from the organism's own embodied tissue.
        gross=min(deficit/(.90*efficiency),embodied*.035,
                  surplus_mass*density)
        if gross<=1e-12:return paid
        toll_work=gross*.10
        tissue_loss=min(surplus_mass,gross/max(density,1e-12))
        b.transform([(live,ph.detritus(a),tissue_loss)],source=tissue,
                    work=toll_work,
                    energy_outputs=[(tissue,'environment:heat',toll_work*.90)])
        metabolic=gross-toll_work
        useful=metabolic*efficiency;lost=metabolic-useful
        transfers=[]
        if lost>1e-12:transfers.append((tissue,'environment:heat',lost))
        if useful>1e-12:transfers.append((tissue,self._short(a),useful))
        if transfers:b.move(energy=transfers)
        if useful>1e-12:
            b.move(energy=[(self._short(a),'environment:heat',useful)])
        # Accelerated body loss reduces condition; no indefinite starvation.
        a.condition=max(0.,a.condition-.0008*tissue_loss/max(body,1e-12))
        self.trophic_metrics['tissue_fuel_mobilized']+=useful
        self.trophic_metrics['catabolized_body_mass']+=tissue_loss
        return paid+useful

    def _diet_role(self,a):
        return CARNIVORE_ROLES.get(a.species)

    def _feed_stock(self,a,source,kind,dt=None):
        if self.trophic_flags['diet'] and source==self.tree.acct('plant',a.habitat) and a.species in PLANT_EATER_ROLES:
            if not a.alive:return False
            dt=getattr(self,'_current_dt',1.) if dt is None else dt
            role=PLANT_EATER_ROLES[a.species]
            body=self._bodymass(a)
            daily=max(.008,body*role.forage_capacity)*self._trait(a).intake
            if a.stage in ('juvenile','dependent'):daily*=.70
            q=min(daily*dt,self._local_access(a,source),
                  max(0.,role.gut_fraction*body-self.book.mass[self.physical.gut(a)]))
            result=self.lots.ingest(a,self.lots.plant(a.habitat),q,role.digestibility,kind)
            if result:self.trophic_metrics['plant_fiber_meals']+=1
            return result
        if not self.trophic_flags['diet'] or not self._diet_role(a) or source!=self.carrion(a.habitat):
            return super()._feed_stock(a,source,kind,dt=dt)
        if not a.alive:return False
        dt=getattr(self,'_current_dt',1.) if dt is None else dt
        role=self._diet_role(a); lot=self.lots.carrion(a.habitat)
        body=self._bodymass(a)
        # Carnivores can take larger, less frequent meals, but digestion and
        # finite gut capacity still limit how much can enter per elapsed day.
        daily=max(.007,body*.24)*self._trait(a).intake
        if a.stage in ('dependent','juvenile'):daily*=.7
        q=min(daily*dt,self._local_access(a,source),
              max(0.,role.stomach_fraction*body-self.book.mass[self.physical.gut(a)]))
        success=self.lots.ingest(a,lot,q,role.meat_digestibility,kind)
        if success:self.trophic_metrics['book_backed_meat_meals']+=1
        return success

    def _digest(self,a,dt=1.):
        before=self.book.energy[self.physical.reserve(a)]
        super()._digest(a,dt=dt)
        if not self.trophic_flags['diet'] or not self._diet_role(a):return
        # Move existing surplus short-term fuel into sustainable reserve, never
        # create a meal or alter maintenance demand. Fasting capacity is a trait.
        role=self._diet_role(a);short=self._short(a);reserve=self.physical.reserve(a)
        short_goal=max(.001,self._maintenance_demand(a)*2.)
        target=max(.002,self._maintenance_demand(a)*role.reserve_days)
        q=min(max(0.,self.book.energy[short]-short_goal),
              max(0.,target-self.book.energy[reserve]))
        if q>1e-12:
            self.book.move(energy=[(short,reserve,q)])
            self.trophic_metrics['reserve_store_energy']+=q
        self.trophic_metrics['carnivore_digestions']+=1

    def _choose(self,a):
        action,hunger,danger=super()._choose(a)
        if not self.trophic_flags['diet'] or not self._diet_role(a):return action,hunger,danger
        if a.stage=='dependent' or action in ('flee','hide','sleep') or danger:return action,hunger,danger
        state=self._state(a)
        if state.fatigue>.72 or state.readiness<.28:return action,hunger,danger
        role=self._diet_role(a)
        reserve=self.book.energy[self.physical.reserve(a)]
        short=self.book.energy[self._short(a)]
        gut=self.book.energy[self._gut_energy(a)]
        need=max(1e-9,self._maintenance_demand(a))
        # Satiety tracks supply in days of physiological maintenance rather
        # than a flat unit tax. Stored gut content is not fully assimilated yet.
        coverage=(reserve*.60+short+gut*.30)/need
        if gut>need*4 and coverage>=3.5:
            self.trophic_metrics['fed_predator_rest_decisions']+=1
            return 'rest',0.,False
        if coverage<min(8.,role.reserve_days*.26) and gut<need*5:
            self.trophic_metrics['hungry_predator_search_decisions']+=1
            return 'feed',max(hunger,.55),False
        return action,hunger,danger

    def _scavenge(self,a):
        if not self._diet_role(a):return False
        source=self.carrion(a.habitat)
        if self._local_access(a,source)<.00001 and self.eco_flags.spatial:
            # Carcasses need to be found in a reachable microcell: habitat-wide
            # stocks cannot be eaten from arbitrary locations. Adjacent scent
            # investigation resolves one real, Book-funded movement when able.
            st=self._state(a)
            now=(self.day-1)+getattr(self,'_substep_index',0)*getattr(self,'_current_dt',.25)
            if now+1e-9>=getattr(st,'motion_ready_at',-1.):
                near=self._neighbors(self._pos(a))
                candidates=[(self._cell_quota.get((source,*p),0.),p) for p in near]
                if candidates:
                    amount,best=max(candidates,key=lambda x:(x[0],x[1]))
                    if amount>.00001 and self._work(a,'scavenge_movement',effort=.40):
                        self.positions[a.id]=best
                        st.motion_ready_at=now+.34
                        self.trophic_metrics['paid_carcass_search_steps']+=1
        if self._local_access(a,source)<.00001:return False
        fed=self._feed_stock(a,source,'reused_carcass')
        if fed:self.trophic_metrics['scavenge_meals']+=1
        return fed

    def _hunt(self,a):
        if not self.predation_enabled:
            self.life_metrics['predation_test_suppressed']+=1
            return self._scavenge(a) if self.trophic_flags['hunting'] else False
        if not self.trophic_flags['hunting'] or a.species not in CARNIVORE_ROLES:
            return super()._hunt(a)
        if not a.alive:return False
        # Shrews use separately conserved ant-worker feeding (colony isn't killed).
        if a.species=='insectivore_shrew' and self._ant_worker_take(a):return True
        if a.species not in PREY:return self._scavenge(a)
        role=self._diet_role(a);state=self._state(a)
        gut_mass=self.book.mass[self.physical.gut(a)];body=self._bodymass(a)
        capacity=role.stomach_fraction*body
        # Physiology limits hunting after a meal. This protects prey through
        # real satiation, not by imposing a species-level population floor.
        if gut_mass>=capacity*.72:
            self.trophic_metrics['satiated_hunt_deferred']+=1
            return False
        now=(self.day-1)+getattr(self,'_substep_index',0)*getattr(self,'_current_dt',.25)
        if now+1e-9<getattr(state,'handling_until',-1.):
            self.trophic_metrics['handling_hunt_deferred']+=1
            return self._scavenge(a)
        nearby=[p for p in self.actors.values() if p.alive and p.id!=a.id and
                p.species in PREY.get(a.species,()) and p.habitat==a.habitat]
        if self.eco_flags.spatial:
            here=self._pos(a)
            nearby=[p for p in nearby if abs(self._pos(p)[1]-here[1])+abs(self._pos(p)[2]-here[2])<=1]
        if not nearby:return self._scavenge(a)
        # A low-density refuge effect arises from the cover and encounter rate;
        # every prey animal retains a nonzero chance of being found.
        habitat_count=sum(p.alive and p.habitat==a.habitat and
                          p.species in PREY[a.species] for p in self.actors.values())
        encounter=habitat_count/(habitat_count+1.4*role.refuge_sensitivity)
        visible=[]
        for p in nearby:
            cover=HABITAT_REFUGE.get(p.habitat,.40)
            burrow=PREY_SHELTER.get(p.species,.10)
            detection=max(.025,min(.96, (.85-.35*cover-.22*burrow-
                         (.32 if p.hidden else 0.))*encounter*self._trait(a).sense))
            if self.rng.random()<detection:visible.append(p)
        if not visible:
            self.trophic_metrics['missed_encounters']+=1
            return self._scavenge(a)
        # Prefer safe, accessible prey and larger digestible return; do not use
        # omniscient global state. Rng tie-break keeps seeds reproducible.
        def score(p):
            prey_mass=self.book.mass[self.physical.live(p)]
            preference=PREY_PREFERENCE.get(a.species,{}).get(p.species,1.)
            # Intake return adjusted by actual species specialization and
            # injury risk, rather than favoring all large prey by default.
            return (min(prey_mass,capacity)*.65/(.16+p.avoid_skill) *
                    (1.-.24*PREY_SHELTER.get(p.species,.10))*preference)
        victim=max(visible,key=lambda p:(score(p),p.id))
        intraguild=victim.species in CARNIVORE_ROLES
        effort=1.55*role.pursuit_effort*(2.4 if intraguild else 1.)
        if not self._work(a,'strike',effort=effort):return False
        if intraguild:self.trophic_metrics['intraguild_attacks']+=1
        self.trophic_metrics['book_funded_strikes']+=1
        self._log('hunt_attempt',actor=a.id,prey=victim.id,habitat=a.habitat)
        cover=HABITAT_REFUGE.get(a.habitat,.4)
        chance=max(.03,min(.82,(.24+.28*a.hunt_skill+
                .12*(victim.stage=='dependent')-.18*victim.avoid_skill-
                .09*cover-(.12 if victim.hidden else 0.))*
                max(.27,(1.-.34*state.fatigue)*state.readiness)))
        if intraguild:chance*=.38  # defensive agility and high confrontation risk
        if self.rng.random()>=chance:
            victim.avoid_skill=min(1.,victim.avoid_skill+.003)
            self.trophic_metrics['failed_strikes']+=1
            self._log('escape',actor=victim.id,predator=a.id,habitat=victim.habitat)
            return self._scavenge(a)
        b=self.book;ph=self.physical
        live=ph.live(victim);preymass=b.mass[live]
        eaten=min(preymass*.72,max(0.,capacity-gut_mass))
        if eaten<0:eaten=0.
        carrion=self.carrion(a.habitat)
        if preymass>1e-12:
            legs=[(live,carrion,preymass-eaten)]
            if eaten>1e-12:legs.append((live,ph.gut(a),eaten))
            ph.convert([(s,d,q) for s,d,q in legs if q>1e-12])
        tissue=ph.tissue(victim); embodied=b.energy[tissue]
        into_gut=embodied*eaten/max(preymass,1e-12)
        carcass_energy=ph.carrion_energy(a.habitat)
        if embodied>1e-12:
            legs=[]
            if into_gut>1e-12:legs.append((tissue,self._gut_energy(a),into_gut))
            if embodied-into_gut>1e-12:legs.append((tissue,carcass_energy,embodied-into_gut))
            b.move(energy=legs)
        if into_gut>1e-12:
            state.gut_quality_weight+=into_gut*role.meat_digestibility
            state.gut_energy_weight+=into_gut
        for key in (ph.maternal(victim),ph.gut(victim)):
            q=b.mass[key]
            if q>1e-12:ph.convert([(key,carrion,q)])
        for key in (ph.maternal_energy(victim),self._gut_energy(victim),
                    ph.reserve(victim),self._short(victim)):
            energy=b.energy[key]
            if energy>1e-12:b.move(energy=[(key,carcass_energy,energy)])
        victim.alive=False;victim.pregnant_until=None;victim.pregnancy_father=None
        for other in self.actors.values():other.caregiver_ids.discard(victim.id)
        a.hunt_skill=min(1.,a.hunt_skill+.0035)
        state.handling_until=now+role.handling_days
        self.trophic_metrics['successful_kills']+=1
        if intraguild:self.trophic_metrics['intraguild_kills']+=1
        self.trophic_metrics['embodied_meat_energy_to_gut']+=into_gut
        self._log('death',actor=victim.id,species=victim.species,
                  cause='predation',habitat=victim.habitat)
        self._log('predation',predator=a.id,prey=victim.id,habitat=a.habitat,
                  prey_mass=preymass,consumed=eaten)
        return True

    def _care(self,a,episode='primary'):
        done=super()._care(a,episode=episode)
        if not self.trophic_flags['provisioning'] or not self._diet_role(a):return done
        if a.stage not in ('adult','elder'):return done
        dependents=[p for p in self.actors.values() if p.alive and
                    p.stage=='dependent' and a.id in p.caregiver_ids and
                    p.habitat==a.habitat and p.species==a.species]
        for child in dependents:
            if self._child_fed_day.get(child.id)==self.day:continue
            if self.eco_flags.spatial and self._pos(a)!=self._pos(child):continue
            gut=self.physical.gut(a);gm=self.book.mass[gut]
            available=max(0.,gm-self._bodymass(a)*.035)
            q=min(available*.24, self._bodymass(child)*.12,
                  max(0.,.22*self._bodymass(child)-self.book.mass[self.physical.gut(child)]))
            if q<=.0002:continue
            ge=self._gut_energy(a); e=self.book.energy[ge]*q/max(gm,1e-12)
            quality=self._state(a).gut_quality_weight/max(self._state(a).gut_energy_weight,1e-12)
            # Gut-to-gut is spatial transfer of unchanged food material, not
            # a material-state transformation (Book rejects same-state transform).
            self.book.move(material=[(gut,self.physical.gut(child),q)])
            if e>1e-12:
                self.book.move(energy=[(ge,self._gut_energy(child),e)])
                self._state(child).gut_energy_weight+=e
                self._state(child).gut_quality_weight+=e*min(1.,quality)
                parent=self._state(a)
                parent.gut_energy_weight=max(0.,parent.gut_energy_weight-e)
                parent.gut_quality_weight=max(0.,parent.gut_quality_weight-e*quality)
            self._child_fed_day[child.id]=self.day
            self.trophic_metrics['regurgitated_child_meals']+=1
            done=True
        return done


class UnifiedCoreCompletion146(UnifiedCoreCompletion145):
    def __init__(self,*args,trophic_diet=True,trophic_hunting=True,
                 trophic_provisioning=True,**kwargs):
        super().__init__(*args,**kwargs)
        if type(self.bridge) is not CoreCompletionBridge145:
            raise TypeError('unexpected Core145 bridge')
        self.bridge.__class__=CoreCompletionBridge146
        self.bridge.activate_trophic(diet=trophic_diet,hunting=trophic_hunting,
                                    provisioning=trophic_provisioning)
        if trophic_diet or trophic_hunting:
            old=self.bridge.lots
            self.bridge.lots=TrophicInventory146(self.bridge)
            self.bridge.lots.metrics.update(old.metrics)
            self.bridge.lots._last_photo_age=dict(getattr(old,'_last_photo_age',{}))
            self.bridge.tree._five_phase_inventory=self.bridge.lots
        assert self.host.book is self.bridge.book is self.bridge.tree.book
        self.host.book.audit()

    def report(self):
        r=super().report()
        r['core_completion_146']={'status':'experimental_not_canonical',
            'trophic_features':dict(self.bridge.trophic_flags),
            'trophic_metrics':dict(self.bridge.trophic_metrics),
            'one_book':self.host.book is self.bridge.book is self.bridge.tree.book}
        return r
