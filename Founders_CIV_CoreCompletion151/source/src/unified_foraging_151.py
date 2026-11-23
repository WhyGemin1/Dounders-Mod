"""Core151: unify predator appetite, meat use and strike permission.

All physical movements, kills, material and energy transfers continue to be
settled by the native Book through Core150. The policy neither mints resources
nor imposes fixed kills/day or population floors. It constrains redundant
hunting using existing physiology, gut space and real (not promised) nutrition.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from math import isfinite
from core_physiology_v2 import PROFILES

from integration_cleanup_150 import UnifiedCleanup150, CleanBridge150
from trophic_roles_146 import CARNIVORE_ROLES
from core_physiology_v2 import PREY


@dataclass(frozen=True)
class ForagingState151:
    """Derived assessment, not an owned wallet or persistent resource."""
    gut_mass: float
    stomach_capacity: float
    circulating_energy: float
    stored_energy: float
    gut_energy: float
    daily_maintenance: float
    available_days: float
    edible_carrion_mass: float
    nutritional_need: bool
    has_gut_room: bool


# Demand buffer: how long an animal can meet baseline needs without fresh food.
# These are *decision thresholds*, not energy grants or imposed meal schedules.
# Species-specific provisional calibration; all rely on dynamic Book balances.
TARGET_MAINTENANCE_DAYS = {
    'ridge_hound': 11.0,
    'red_fox': 10.0,
    'golden_jackal': 10.0,
    'insectivore_shrew': 2.0,
    'carrion_bird': 7.0,
}


class RegulatedForagingBridge151(CleanBridge150):
    def activate_regulation151(self, enabled=True, carrion_tracking=True, intraguild_risk=False):
        self.regulation151_enabled = bool(enabled)
        self.carrion_tracking151 = bool(carrion_tracking)
        self.intraguild_risk151 = bool(intraguild_risk)
        self.regulation151_metrics = Counter()

    def _fatal_condition(self, animal, state):
        """Biological failure requires irrecoverable physical depletion.

        The inherited .98 starvation *score* used to kill an animal while it
        still had healthy condition and substantial tissue energy. That score
        is now a stress signal: sustained scarcity worsens real condition.
        Death is still possible through critical condition or simultaneous
        body depletion, fuel depletion and prolonged scarcity. This does NOT
        restore energy or give any species immunity to starvation.
        """
        if not self.regulation151_enabled:
            return super()._fatal_condition(animal,state)
        if animal.condition<=.06:
            return True
        p=PROFILES[animal.species]
        b=self.book;ph=self.physical
        body=b.mass[ph.live(animal)]
        critical=(p.newborn_mass()*.70 if animal.stage=='dependent' else
                  p.adult_mass()*(.13 if animal.stage=='juvenile' else .16))
        accessible=(b.energy[ph.reserve(animal)]+b.energy[self._short(animal)]+
                    .50*b.energy[self._gut_energy(animal)])
        physiological_collapse=(state.starvation_debt>=.98 and
            body<=critical and accessible<self._maintenance_demand(animal)*.40)
        if physiological_collapse:self.regulation151_metrics['critical_body_depletion_deaths']+=1
        return physiological_collapse

    def _emergency_tissue_to_fuel(self,animal,requested):
        """Rate-limited conversion of existing body tissue to circulating fuel.

        Preserve protein/structural minimum; the old FuelFlex floor at 35% of
        adult mass prevented any work while food might be locally available.
        An expensive emergency burst can mobilize remaining nonessential tissue
        *before* a strike; each consumed unit leaves body mass and tissue Book.
        """
        if not self.regulation151_enabled:
            return super()._emergency_tissue_to_fuel(animal,requested)
        if requested<=1e-12 or not animal.alive:return 0.
        b=self.book;ph=self.physical;p=PROFILES[animal.species]
        body=b.mass[ph.live(animal)];tissue=ph.tissue(animal)
        available=b.energy[tissue]
        # Young animals have a stage-dependent mass minimum, not a fixed
        # adult threshold that can exceed the mass of a healthy newborn.
        floor=(p.newborn_mass()*.65 if animal.stage=='dependent' else
               p.adult_mass()*(.14 if animal.stage=='juvenile' else .18))
        surplus=max(0.,body-floor)
        if surplus<=1e-12 or available<=1e-12:return 0.
        density=available/max(body,1e-12)
        yield_fraction=.90*.75
        gross=min(requested/yield_fraction,available*.042,surplus*density*.085)
        useful=gross*yield_fraction
        if useful+1e-11<requested:return 0.
        lost_mass=gross/max(density,1e-12)
        toll=.10*gross
        b.transform([(ph.live(animal),ph.detritus(animal),lost_mass)],
                    source=tissue,work=toll,
                    energy_outputs=[(tissue,'environment:heat',toll*.90)])
        fuel=(gross-toll)*.75
        heat=(gross-toll)-fuel
        b.move(energy=[(tissue,self._short(animal),fuel),
                       (tissue,'environment:heat',heat)])
        animal.condition=max(0.,animal.condition-.004*lost_mass/max(body,1e-12))
        self.regulation151_metrics['tissue_to_fuel_energy']+=fuel
        self.regulation151_metrics['tissue_to_fuel_mass']+=lost_mass
        return fuel

    def _work(self,animal,activity,effort=1.0):
        """Permit a costly real strike from somatic substrate if prey is near.

        Inherited low-intensity recovery already uses this conversion; this
        additional high-intensity path applies only when hungry and actual
        locally reachable prey exist. Work remains limited by physiological
        power, with an ordinary Book debit even on unsuccessful hunting.
        """
        if (self.regulation151_enabled and activity=='strike' and
            self.fuel_flex_enabled and self.predation_enabled and
            animal.species in CARNIVORE_ROLES and animal.alive and
            self._foraging_state151(animal).nutritional_need):
            here=self._pos(animal)
            nearby=any(x.alive and x.id!=animal.id and
                x.species in PREY.get(animal.species,()) and
                x.habitat==animal.habitat and
                (not self.eco_flags.spatial or
                abs(self._pos(x)[1]-here[1])+abs(self._pos(x)[2]-here[2])<=1)
                for x in self.actors.values())
            if nearby:
                state=self._state(animal);trait=self._trait(animal)
                scale=(self._bodymass(animal)/.05)**.64
                learned=1.+min(.5,state.experience*.20)
                readiness=max(.20,state.readiness)
                efficiency=max(.35,(1.-.34*state.fatigue)*readiness*learned)
                demand=.000055*scale*(effort/max(.1,trait.locomotion))/max(efficiency,.1)
                immediate=self.book.energy[self._short(animal)]
                reserve=self.book.energy[self.physical.reserve(animal)]
                ordinary=immediate+min(reserve,self._mobilization_capacity(animal))
                if demand>ordinary+1e-12:
                    recovered=self._emergency_tissue_to_fuel(animal,demand-ordinary)
                    if recovered>0:
                        self.regulation151_metrics['emergency_strike_fuel']+=recovered
        return super()._work(animal,activity,effort)

    def _foraging_state151(self, animal):
        """Single physical accounting view for decisions AND attack eligibility."""
        role = CARNIVORE_ROLES[animal.species]
        b = self.book
        ph = self.physical
        cap = max(1e-10, role.stomach_fraction * self._bodymass(animal))
        gm = max(0., b.mass[ph.gut(animal)])
        ge = max(0., b.energy[self._gut_energy(animal)])
        rapid = max(0., b.energy[self._short(animal)])
        stored = max(0., b.energy[ph.reserve(animal)])
        # The gut's energy remains subject to digestion; it is NOT equivalent
        # to already circulating fuel. Reserve is rate-limited by FuelFlex147.
        maintenance = max(1e-12, self._maintenance_demand(animal))
        available = rapid + stored * .78 + ge * .55
        days = available / maintenance
        target = TARGET_MAINTENANCE_DAYS[animal.species]
        if animal.stage in ('dependent', 'juvenile'):
            target *= 1.20
        # Maternal development remains governed by Core145 nutrient allocation.
        if animal.sex == 'F' and animal.stage == 'adult':
            target *= 1.15
        # No synthetic energy is added by a target. Decline in actual reserves,
        # gut assimilation, or elevated work all change the decision naturally.
        need = days < target
        room = gm < cap * .72
        # Carcasses are per-cell accessible from the existing Book-backed quota,
        # not globally omniscient. This access is not a new inventory.
        carrion = self.carrion(animal.habitat)
        accessible = max(0., self._local_access(animal, carrion))
        if not all(isfinite(v) for v in (gm,ge,rapid,stored,maintenance,days,accessible)):
            raise AssertionError('nonfinite predator physiology')
        return ForagingState151(gm,cap,rapid,stored,ge,maintenance,days,
                               accessible,need,room)

    def _choose(self, animal):
        # Core150 retains exclusive responsibility for prey/plant-eaters,
        # acute danger, dependent offspring, and sleep physiology.
        action, hunger, danger = super()._choose(animal)
        if not self.regulation151_enabled or animal.species not in CARNIVORE_ROLES:
            return action, hunger, danger
        if not animal.alive or animal.stage == 'dependent':
            return action, hunger, danger
        if danger or action in ('flee','hide','sleep','care','stay_with_caregiver'):
            return action, hunger, danger
        st = self._state(animal)
        # A mate search is a physical and distinct goal. Let the inherited
        # physically paid mate migration resolve; do not silently force kills.
        if (action == 'search' and self.ecoregulation_flags.get('mate_search',False)
            and self._foraging_state151(animal).available_days >= 4.0):
            if self._local_mate_habitats(animal):
                self.regulation151_metrics['mate_priority_decisions'] += 1
                return action,hunger,danger
        if st.fatigue > .70 or st.readiness < .28:
            self.regulation151_metrics['physiological_recovery_decisions'] += 1
            return 'rest',hunger,False
        state = self._foraging_state151(animal)
        if not state.has_gut_room:
            self.regulation151_metrics['gut_satiation_decisions'] += 1
            return 'rest', 0., False
        if not state.nutritional_need:
            self.regulation151_metrics['reserve_satiation_decisions'] += 1
            return 'rest', 0., False
        # Distinguish useful carrion from microscopic traces. Its energy must
        # fund at least a material fraction of current maintenance, assessed
        # at the local carcass's real embodied energy density.
        local = min(state.edible_carrion_mass,
                    state.stomach_capacity-state.gut_mass)
        density = self._carcass_energy_offer(animal,local)/max(local,1e-12) if local>0 else 0.
        quality = CARNIVORE_ROLES[animal.species].meat_digestibility
        if local * density * quality >= state.daily_maintenance*.35:
            self.regulation151_metrics['carrion_plans'] += 1
            return 'feed',max(hunger,.55),False
        self.regulation151_metrics['hunt_plans'] += 1
        return 'feed',max(hunger,.55),False

    def _migrate(self, animal, decision=None):
        """Choose a useful carcass location before wandering after fresh prey.

        Core148 tracking previously searched for moving prey even where a
        locally recorded, energy-bearing carcass was within scent range.
        Locomotion remains one real funded step; no instant ingestion or attack
        after movement within the same elapsed-time substep.
        """
        if (not self.regulation151_enabled or not self.carrion_tracking151
            or animal.species not in CARNIVORE_ROLES or decision not in ('feed','search')
            or not self.eco_flags.spatial or not animal.alive
            or not self.integration149_flags.get('carcass_locality',False)):
            return super()._migrate(animal,decision)
        state=self._foraging_state151(animal)
        if not state.nutritional_need or not state.has_gut_room:
            return False
        # Existing local food should be eaten, not abandoned while the generic
        # predator-tracking mechanism follows a different moving prey animal.
        local=min(state.edible_carrion_mass,state.stomach_capacity-state.gut_mass)
        if local>1e-9:
            e=self._carcass_energy_offer(animal,local)
            if e*CARNIVORE_ROLES[animal.species].meat_digestibility >= .35*state.daily_maintenance:
                self.regulation151_metrics['local_carrion_not_abandoned']+=1
                return False
        # Safe mate cues may override hunting only when the animal has enough
        # reserves to support courting and movement; severe hunger takes priority.
        if decision=='search' and state.available_days>=4.0 and self._local_mate_habitats(animal):
            return super()._migrate(animal,decision)
        now=self._physical_time()
        st=self._state(animal)
        if now+1e-9 < getattr(st,'motion_ready_at',-1.):
            return False
        here=self._pos(animal)
        role=CARNIVORE_ROLES[animal.species]
        radius=max(2,role.scent_radius)
        choices=[]
        for patch,mass in self._carcass_patches149.items():
            if patch[0]!=animal.habitat or mass<=1e-9:continue
            dist=abs(patch[1]-here[1])+abs(patch[2]-here[2])
            if dist<1 or dist>radius:continue
            patch_energy=max(0.,self._carcass_energy_patches150.get(patch,0.))
            useful=patch_energy*role.meat_digestibility
            if useful < .20*state.daily_maintenance:continue
            choices.append((useful/(1.+dist),-dist,patch))
        if not choices:
            return super()._migrate(animal,decision)
        destination=max(choices)[2]
        options=self._neighbors(here)
        viable=[p for p in options if abs(p[1]-destination[1])+abs(p[2]-destination[2])<
                abs(here[1]-destination[1])+abs(here[2]-destination[2])]
        if not viable:return super()._migrate(animal,decision)
        target=min(viable,key=lambda p:(abs(p[1]-destination[1])+abs(p[2]-destination[2]),p))
        if not self._work(animal,'scavenge_movement',effort=.40):
            self.regulation151_metrics['carrion_tracking_unfunded']+=1
            return False
        self.positions[animal.id]=target
        st.last_carrion_step=(self.day,getattr(self,'_substep_index',0))
        self.regulation151_metrics['paid_carrion_tracking_steps']+=1
        return True

    def _hunt(self, animal):
        if (not self.regulation151_enabled or animal.species not in CARNIVORE_ROLES
            or not self.predation_enabled or not self.trophic_flags['hunting']):
            return super()._hunt(animal)
        if getattr(self._state(animal),'last_carrion_step',None)==(self.day,getattr(self,'_substep_index',0)):
            self.regulation151_metrics['strike_deferred_after_carrion_tracking']+=1
            return False
        # The execution gate reads the SAME dynamically updated state as the
        # decision resolver, avoiding mutually contradictory appetite rules.
        state=self._foraging_state151(animal)
        if not state.has_gut_room or not state.nutritional_need:
            self.regulation151_metrics['unnecessary_strikes_prevented'] += 1
            return False
        role=CARNIVORE_ROLES[animal.species]
        # Reserve the first nutritional opportunity for real nearby carrion;
        # a failed scavenging attempt does not manufacture food or cancel a
        # physically necessary hunt.
        potential=min(state.edible_carrion_mass,state.stomach_capacity-state.gut_mass)
        e=self._carcass_energy_offer(animal,potential) if potential>0 else 0.
        if e*role.meat_digestibility>=state.daily_maintenance*.35:
            if self._scavenge(animal):
                self.regulation151_metrics['carrion_consumed_before_strike'] += 1
                return True
        # Intraguild predation is costly and can remove the only founder of a
        # smaller carnivore. The old selector treated an isolated fox/jackal as
        # a normal meal whenever it was the only adjacent target. Use actual
        # sensing and paid pursuit of safer prey before engaging a competitor;
        # extreme hunger still permits a dangerous attack. This is individual
        # risk/reward behavior, NOT a population floor or blanket immunity.
        if self.intraguild_risk151 and self.eco_flags.spatial and animal.species in PREY:
            here=self._pos(animal)
            possible=[p for p in self.actors.values() if p.alive and p.id!=animal.id
                      and p.habitat==animal.habitat and
                      p.species in PREY.get(animal.species,())]
            adjacent=[p for p in possible if abs(self._pos(p)[1]-here[1])+
                       abs(self._pos(p)[2]-here[2])<=1]
            ordinary=[p for p in adjacent if p.species not in CARNIVORE_ROLES]
            competitors=[p for p in adjacent if p.species in CARNIVORE_ROLES]
            if competitors and not ordinary and state.available_days>1.5:
                sensed=[]
                radius=max(2,role.scent_radius)
                for prey in possible:
                    if prey.species in CARNIVORE_ROLES:continue
                    pos=self._pos(prey)
                    dist=abs(pos[1]-here[1])+abs(pos[2]-here[2])
                    if 1<dist<=radius:
                        sensed.append((dist,prey.id,pos))
                if sensed:
                    target=min(sensed)[2]
                    neighbors=self._neighbors(here)
                    steps=[cell for cell in neighbors if
                        abs(cell[1]-target[1])+abs(cell[2]-target[2]) <
                        abs(here[1]-target[1])+abs(here[2]-target[2])]
                    if steps and self._work(animal,'prey_tracking',effort=.32):
                        self.positions[animal.id]=min(steps,key=lambda cell:(
                            abs(cell[1]-target[1])+abs(cell[2]-target[2]),cell))
                        self._state(animal).last_tracking_step=(self.day,getattr(self,'_substep_index',0))
                        self.regulation151_metrics['safer_prey_pursuit_instead_of_intraguild']+=1
                        return False
                # Above the emergency-need boundary, declining a risky fight
                # is a legitimate autonomous choice. Competing carnivores may
                # still fight when severely depleted, with Core146 injury risk.
                self.regulation151_metrics['risky_intraguild_attempts_deferred']+=1
                return self._scavenge(animal)
        # Core146 retains physically funded encounter, escape, pursuit,
        # carcass disposal and kill accounting; Core149/150 retain localized
        # paired-energy ingestion. No second strike is possible this substep.
        return super()._hunt(animal)


class UnifiedRegulatedForaging151(UnifiedCleanup150):
    def __init__(self,*args,regulated_foraging=True,carrion_tracking=True,intraguild_risk=False,**kwargs):
        super().__init__(*args,**kwargs)
        if type(self.bridge) is not CleanBridge150:
            raise TypeError('Cycle151 expects active Core150 bridge')
        self.bridge.__class__=RegulatedForagingBridge151
        self.bridge.activate_regulation151(regulated_foraging,carrion_tracking=carrion_tracking,intraguild_risk=intraguild_risk)
        assert self.host.book is self.bridge.book is self.bridge.tree.book
        self.host.book.audit()

    def report(self):
        r=super().report()
        r['regulated_foraging_151']={'enabled':self.bridge.regulation151_enabled,
            'carrion_tracking':self.bridge.carrion_tracking151,
            'intraguild_risk_experimental':self.bridge.intraguild_risk151,
            'metrics':dict(self.bridge.regulation151_metrics),
            'status':'experimental_not_canonical'}
        return r
