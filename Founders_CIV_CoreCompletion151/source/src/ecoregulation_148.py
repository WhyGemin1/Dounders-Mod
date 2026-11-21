"""Cycle148: local encounter and mate-access repairs on one Core147 physiology.

This is an opt-in, falsifiable ecological treatment, NOT a canonical engine.
No Book mints, no actor time wallets, no prey spawning or guaranteed mating.
Real energy is paid when a locally perceived animal physically moves.
The ecological goal is to make energy available in space (rather than in a
habitat-wide omniscient index) while retaining legitimate failure paths.
"""
from __future__ import annotations
from collections import Counter
from fuel_flex_147 import UnifiedFuelFlex147, FuelFlexBridge147
from core_physiology_v2 import PREY, PROFILES, ANTS, MEGA
from trophic_roles_146 import CARNIVORE_ROLES, PREY_PREFERENCE
from trophic_guilds_cycle138 import ALLOWED_HABITATS


class EcoRegulationBridge148(FuelFlexBridge147):
    def activate_ecoregulation(self, *, tracking=True, mate_search=True):
        self.ecoregulation_flags = {'tracking':bool(tracking), 'mate_search':bool(mate_search)}
        self.ecoregulation_metrics = Counter()

    def _physical_time(self):
        return ((self.day-1) + getattr(self, '_substep_index',0) *
                getattr(self, '_current_dt', .25))

    def _local_mate_habitats(self, actor):
        """Only physically adjacent habitats; no map-wide mate knowledge."""
        neighbors=self.tree.habitats[actor.habitat].neighbors
        if actor.species in MEGA:
            neighbors=[h for h in neighbors if h in ALLOWED_HABITATS[actor.species]]
        return [h for h in neighbors if any(
            other.alive and other.id!=actor.id and other.species==actor.species
            and other.sex!=actor.sex and other.stage=='adult' and other.habitat==h
            and other.condition>=.60
            for other in self.actors.values())]

    def _choose(self, actor):
        action,hunger,danger=super()._choose(actor)
        if not self.ecoregulation_flags['mate_search'] or actor.species==ANTS:
            return action,hunger,danger
        if actor.stage!='adult' or danger or action in ('flee','hide','sleep','care','stay_with_caregiver'):
            return action,hunger,danger
        if actor.condition<.66 or self._state(actor).fatigue>.65:
            return action,hunger,danger
        if not (PROFILES[actor.species].breeding[0] <= self.day%360 <= PROFILES[actor.species].breeding[1]):
            return action,hunger,danger
        if any(other.alive and other.id!=actor.id and other.species==actor.species
               and other.sex!=actor.sex and other.stage=='adult' and
               other.habitat==actor.habitat for other in self.actors.values()):
            return action,hunger,danger
        if self._local_mate_habitats(actor):
            # A physical search is chosen, not a conception event or time token.
            self.ecoregulation_metrics['mate_search_decisions']+=1
            return 'search',hunger,False
        return action,hunger,danger

    def _track_local_prey(self, actor):
        """Optional one-cell pursuit inside actual species sensing distance.

        Run inside the physical movement resolver, before ordinary migrations.
        One paid step is possible per motion-ready event and the strike is
        deferred; no omniscient habitat-wide tracking or free attack.
        """
        if not (self.ecoregulation_flags['tracking'] and self.predation_enabled
                and self.trophic_flags['hunting'] and self.eco_flags.spatial
                and actor.alive and actor.species in CARNIVORE_ROLES
                and actor.species in PREY):
            return None
        here=self._pos(actor)
        prey_types=PREY[actor.species]
        nearby=[p for p in self.actors.values() if p.alive and p.species in prey_types
                and p.habitat==actor.habitat and p.id!=actor.id]
        if any(abs(self._pos(p)[1]-here[1])+abs(self._pos(p)[2]-here[2])<=1 for p in nearby):
            return None  # existing Core146 handles a directly accessible target
        radius=CARNIVORE_ROLES[actor.species].scent_radius
        visible=[]
        for p in nearby:
            pos=self._pos(p)
            dist=abs(pos[1]-here[1])+abs(pos[2]-here[2])
            if 1<dist<=radius:
                preference=PREY_PREFERENCE.get(actor.species,{}).get(p.species,1.)
                visible.append((dist,-preference,p.id,pos))
        if not visible:return None
        target=min(visible)[3]
        options=self._neighbors(here)
        if not options:return False
        best=min(options,key=lambda loc:(abs(loc[1]-target[1])+abs(loc[2]-target[2]),loc))
        if abs(best[1]-target[1])+abs(best[2]-target[2])>=abs(here[1]-target[1])+abs(here[2]-target[2]):
            return False
        if not self._work(actor,'prey_tracking',effort=.32):
            self.ecoregulation_metrics['tracking_work_unfunded']+=1
            return False
        self.positions[actor.id]=best
        self._state(actor).last_tracking_step=(self.day,getattr(self,'_substep_index',0))
        self.ecoregulation_metrics['paid_local_tracking_steps']+=1
        return True

    def _migrate(self, actor, decision=None):
        if decision in ('feed','search'):
            tracking=self._track_local_prey(actor)
            if tracking is not None:return tracking
        if not self.ecoregulation_flags['mate_search'] or actor.species==ANTS:
            return super()._migrate(actor, decision)
        # Resolve mate-oriented migration BEFORE generic opportunistic wandering;
        # one physical movement at a time. Guard by physiological readiness.
        if (actor.alive and actor.stage=='adult' and decision=='search'
            and actor.condition>=.66 and self._state(actor).fatigue<.70):
            now=self._physical_time()
            state=self._state(actor)
            if now+1e-9>=getattr(state,'motion_ready_at',-1.):
                local_mate=any(x.alive and x.id!=actor.id and x.species==actor.species
                    and x.sex!=actor.sex and x.stage=='adult' and x.habitat==actor.habitat
                    for x in self.actors.values())
                if not local_mate:
                    near=self._local_mate_habitats(actor)
                    # A cue does not guarantee discovery: 40% per opportunity.
                    if near and self.rng.random()<.40:
                        target=self.rng.choice(sorted(near))
                        if self._work(actor,'habitat_movement',effort=2.4):
                            origin=actor.habitat
                            actor.habitat=target
                            self.sync_positions()
                            state.motion_ready_at=now+1.0
                            self.ecoregulation_metrics['mate_search_paid_migrations']+=1
                            self._log('migration',actor=actor.id,from_habitat=origin,
                                to_habitat=target,reason='neighbor_mate_cues',
                                cost_model='current_resolved_work')
                            return True
                        self.ecoregulation_metrics['mate_search_unfunded']+=1
        return super()._migrate(actor,decision)

    def _hunt(self, actor):
        if (self.ecoregulation_flags['tracking'] and
            getattr(self._state(actor),'last_tracking_step',None) ==
            (self.day,getattr(self,'_substep_index',0))):
            # A resolved physical tracking step cannot also claim an
            # instantaneous strike in the same world-clock resolution.
            self.ecoregulation_metrics['strike_deferred_after_tracking']+=1
            return self._scavenge(actor)
        return super()._hunt(actor)


class UnifiedEcoRegulation148(UnifiedFuelFlex147):
    def __init__(self,*args,local_tracking=True,mate_search=True,**kwargs):
        super().__init__(*args,**kwargs)
        if type(self.bridge) is not FuelFlexBridge147:
            raise TypeError('Unexpected bridge: cannot layer Cycle148 safely')
        self.bridge.__class__=EcoRegulationBridge148
        self.bridge.activate_ecoregulation(tracking=local_tracking,mate_search=mate_search)
        assert self.host.book is self.bridge.book is self.bridge.tree.book
        self.host.book.audit()

    def report(self):
        r=super().report()
        r['core_completion_148']={'status':'experimental_not_canonical',
           'flags':dict(self.bridge.ecoregulation_flags),
           'metrics':dict(self.bridge.ecoregulation_metrics),
           'one_book':self.host.book is self.bridge.book is self.bridge.tree.book}
        return r
