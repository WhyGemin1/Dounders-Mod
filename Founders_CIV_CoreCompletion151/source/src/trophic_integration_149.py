"""Cycle149: physically conserved kill nutrition, localized carcasses and trait coverage.

Opt-in integration over Core148; Book-owned mass and energy remain authoritative.
The synthetic coefficients are experimental, not calibrated biological values.
"""
from __future__ import annotations
from collections import Counter
from ecoregulation_148 import EcoRegulationBridge148, UnifiedEcoRegulation148
from species_traits_143 import BLUEPRINTS, FIELDS
from core_physiology_v2 import PROFILES, PREY, ANTS, MEGA
from trophic_roles_146 import CARNIVORE_ROLES, PLANT_EATER_ROLES

ALL_ROLES = frozenset(BLUEPRINTS)


class TrophicIntegrationBridge149(EcoRegulationBridge148):
    def activate_integration(self, enabled=True, *, kill_nutrition=True,
                             carcass_locality=True, carcass_preference=True):
        self.integration149_flags = {
            'kill_nutrition': bool(enabled and kill_nutrition),
            'carcass_locality': bool(enabled and carcass_locality),
            'carcass_preference': bool(enabled and carcass_preference),
        }
        self.integration149_enabled = any(self.integration149_flags.values())
        self.integration149_metrics = Counter()
        self._carcass_patches149 = {}  # Book-backed position metadata, NOT inventory.
        self.audit_species_contracts()

    def audit_species_contracts(self):
        """Reject missing individual traits/niches before simulating a World."""
        if set(PROFILES) != ALL_ROLES:
            raise AssertionError('every species must have one life-history profile')
        if set(a.species for a in self.actors.values()) - ALL_ROLES:
            raise AssertionError('unregistered species instantiated')
        for actor in self.actors.values():
            traits=self._trait(actor)
            if not all(getattr(traits,key)>0 for key in FIELDS):
                raise AssertionError('inactive/invalid phenotype')
            if actor.species not in CARNIVORE_ROLES and actor.species not in PLANT_EATER_ROLES and actor.species!=ANTS:
                raise AssertionError('no feeding guild '+actor.species)
        if not all(role.meat_digestibility>0 and role.stomach_fraction>0 for role in CARNIVORE_ROLES.values()):
            raise AssertionError('invalid carnivore role')
        return True

    def _refresh_quota(self):
        old_day=getattr(self, '_quota_day', None)
        super()._refresh_quota()
        if not self.integration149_flags['carcass_locality'] or not self.eco_flags.spatial or old_day==self._quota_day:
            return
        # Newly killed prey is localized, while legacy carcass stock remains a
        # background pool until its physical location has been established.
        for habitat in self.tree.habitats:
            source=self.carrion(habitat)
            real_mass=max(0.,self.book.mass[source])
            patches={key:max(0.,mass) for key,mass in self._carcass_patches149.items()
                     if key[0]==habitat and mass>1e-12}
            total=sum(patches.values())
            if total>real_mass and total>1e-12:
                factor=real_mass/total
                for key in patches:
                    patches[key]*=factor
                    self._carcass_patches149[key]=patches[key]
                total=real_mass
            # Base quota distributes only the *unlocated* background portion.
            background_fraction=(max(0.,real_mass-total)/real_mass) if real_mass>1e-12 else 0.
            for key in tuple(self._cell_quota):
                if key[0]==source and key[1]==habitat:
                    self._cell_quota[key]*=background_fraction
            for (_,x,y),mass in patches.items():
                self._cell_quota[(source,habitat,x,y)]=self._cell_quota.get((source,habitat,x,y),0.)+mass
        self.integration149_metrics['localized_quota_refreshes']+=1

    def _spend_forage_quota(self, animal, source, amount):
        if not self.integration149_flags['carcass_locality'] or source!=self.carrion(animal.habitat):
            return super()._spend_forage_quota(animal,source,amount)
        cells=list(self._forage_cells(animal,source))
        previous={cell:self._cell_quota.get((source,*cell),0.) for cell in cells}
        result=super()._spend_forage_quota(animal,source,amount)
        for cell in cells:
            used=max(0.,previous[cell]-self._cell_quota.get((source,*cell),0.))
            key=tuple(cell)
            self._carcass_patches149[key]=max(0.,self._carcass_patches149.get(key,0.)-used)
        return result

    def _ant_worker_take(self, shrew):
        """Shrew eats physical ant-worker tissue, then digests it over time.

        The inherited guild branch transferred worker energy instantly into
        reserve. This was an unintentional second digestive economy. Colony
        worker biomass and its embodied energy instead enter the same Book
        gut accounts used by every other animal, with queen survival bounded.
        """
        if not self.integration149_enabled or shrew.species!='insectivore_shrew':
            return super()._ant_worker_take(shrew)
        from trophic_guilds_cycle138 import MIN_QUEEN_MASS
        colony_candidates=[x for x in self.actors.values()
            if x.alive and x.species=='ant_colony' and x.habitat==shrew.habitat
            and (not self.eco_flags.spatial or
                 abs(self._pos(shrew)[1]-self._pos(x)[1])+
                 abs(self._pos(shrew)[2]-self._pos(x)[2])<=1)]
        if not colony_candidates:return False
        colony=max(colony_candidates,key=lambda x:self.book.mass[self.physical.live(x)])
        physical=self.physical;book=self.book
        source=physical.live(colony);body=book.mass[source]
        gut=physical.gut(shrew)
        role=CARNIVORE_ROLES[shrew.species]
        room=max(0.,role.stomach_fraction*self._bodymass(shrew)-book.mass[gut])
        q=min(.0015,max(0.,body-MIN_QUEEN_MASS),room)
        if q<.0001:return False
        tissue=physical.tissue(colony)
        energy=min(book.energy[tissue],book.energy[tissue]*q/max(body,1e-12))
        physical.convert([(source,gut,q)])
        if energy>1e-12:
            book.move(energy=[(tissue,self._gut_energy(shrew),energy)])
            state=self._state(shrew)
            state.gut_energy_weight+=energy
            state.gut_quality_weight+=energy*role.meat_digestibility
        self.integration149_metrics['delayed_ant_worker_meals']+=1
        self.integration149_metrics['ant_worker_gut_mass']+=q
        self._log('ant_worker_ingested',predator=shrew.id,colony=colony.id,
                  mass=q,into_gut_energy=energy,absorbed_immediately=0.)
        return True

    def _hunt(self, predator):
        if not (self.integration149_enabled and self.predation_enabled
                and self.trophic_flags['hunting'] and predator.species in CARNIVORE_ROLES):
            return super()._hunt(predator)
        # The existing kill is energetically valuable as long as meat remains
        # in the local World. Don't needlessly create another carcass before
        # using accessible leftovers; allow scavenging to fail naturally.
        if self.integration149_flags['carcass_preference'] and self._diet_role(predator):
            source=self.carrion(predator.habitat)
            role=self._diet_role(predator)
            gut=self.book.mass[self.physical.gut(predator)]
            body=self._bodymass(predator)
            local_meat=self._local_access(predator,source)
            current_dt=getattr(self,'_current_dt',.25)
            # Tiny carcass traces cannot replace a substantial meal. Compare
            # expected usable nutritional energy with actual maintenance,
            # rather than blindly avoiding hunts whenever a trace exists.
            candidate_mass=min(local_meat, max(0.,role.stomach_fraction*body-gut),
                               max(.007,body*.24)*current_dt*self._trait(predator).intake)
            projected_energy=candidate_mass*self.lots.carrion(predator.habitat).nominal_density*role.meat_digestibility
            sufficiently_nutritious=projected_energy>=self._maintenance_demand(predator)*1.5
            if gut<role.stomach_fraction*body*.72 and sufficiently_nutritious:
                if self._scavenge(predator):
                    self.integration149_metrics['carcass_preferred_over_kill']+=1
                    return True
        # Take only physical pre-kill body energy and exact victim identity;
        # no new RNG draws, no global teleport, no modified conception rules.
        possible={x.id:x for x in self.actors.values() if x.alive and x.id!=predator.id
                  and x.species in PREY.get(predator.species,())
                  and x.habitat==predator.habitat}
        prior={uid:(self.book.energy[self.physical.reserve(x)]+
                    self.book.energy[self._short(x)]) for uid,x in possible.items()}
        source=self.carrion(predator.habitat)
        carrion_before=self.book.mass[source]
        result=super()._hunt(predator)
        newly_dead=[x for x in possible.values() if not x.alive]
        if not newly_dead:
            return result
        if len(newly_dead)>1:
            raise AssertionError('one strike killed multiple prey')
        victim=newly_dead[0]
        role=self._diet_role(predator)
        carrion_after=self.book.mass[source]
        new_remains=max(0.,carrion_after-carrion_before)
        if self.integration149_flags['carcass_locality'] and self.eco_flags.spatial and new_remains>1e-12:
            location=self._pos(victim)
            key=tuple(location)
            self._carcass_patches149[key]=self._carcass_patches149.get(key,0.)+new_remains
            # The Book has already gained real carcass mass. Add only to
            # local *access metadata*, not to physical inventory.
            qkey=(source,*location)
            self._cell_quota[qkey]=self._cell_quota.get(qkey,0.)+new_remains
            self.integration149_metrics['carcass_mass_localized']+=new_remains
        # The prey's endogenous reserve/rapid fuel represents energy in its
        # edible flesh. Core146 placed all of it in carcass; the hunter already
        # ate part of that flesh. Transfer that same proportional part from
        # carcass into the hunter's gut -- no free predator energy bonus.
        logs=[e for e in reversed(self.events[-12:]) if e.get('event')=='predation'
              and e.get('prey')==victim.id] if hasattr(self,'events') else []
        if not logs:
            self.integration149_metrics['kill_without_accessible_log']+=1
            return result
        kill=logs[0]
        prey_mass=max(1e-12,float(kill.get('prey_mass',0.)))
        eaten=max(0.,float(kill.get('consumed',0.)))
        proportion=min(1.,eaten/prey_mass)
        carried=prior.get(victim.id,0.)*proportion
        carcass_energy=self.physical.carrion_energy(predator.habitat)
        reward=min(carried,self.book.energy[carcass_energy])
        if self.integration149_flags['kill_nutrition'] and reward>1e-12:
            self.book.move(energy=[(carcass_energy,self._gut_energy(predator),reward)])
            state=self._state(predator)
            state.gut_energy_weight+=reward
            state.gut_quality_weight+=reward*role.meat_digestibility
            self.integration149_metrics['previously_stranded_prey_fuel_to_gut']+=reward
        self.integration149_metrics['kills_with_conserved_reward']+=1
        return result


class UnifiedTrophicIntegration149(UnifiedEcoRegulation148):
    def __init__(self,*args,trophic_integration=True,kill_nutrition=True,
                 carcass_locality=True,carcass_preference=True,**kwargs):
        super().__init__(*args,**kwargs)
        if type(self.bridge) is not EcoRegulationBridge148:
            raise TypeError('Cycle149 requires active Core148 bridge')
        self.bridge.__class__=TrophicIntegrationBridge149
        self.bridge.activate_integration(enabled=trophic_integration,
            kill_nutrition=kill_nutrition,carcass_locality=carcass_locality,
            carcass_preference=carcass_preference)
        assert self.host.book is self.bridge.book is self.bridge.tree.book
        self.host.book.audit()

    def report(self):
        result=super().report()
        result['trophic_integration_149']={
            'enabled':self.bridge.integration149_enabled,
            'flags':dict(self.bridge.integration149_flags),
            'metrics':dict(self.bridge.integration149_metrics),
            'species_contracts':len(ALL_ROLES),
            'status':'experimental_not_canonical'}
        return result
