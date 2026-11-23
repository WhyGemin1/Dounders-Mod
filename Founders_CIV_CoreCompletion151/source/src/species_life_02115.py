"""Experimental v0.21.7 life-history/needs adapter for the WORLD-023 Book.

These fields are *transcribed* from v0.21.7 biology/ecology.py SpeciesProfile
and biology/species_needs.py NeedsTrait. Do not interpret synthetic pilot
parameters as real population calibration. The separate v0.21.7 ecology is
NOT stepped: this module maps its life-history rules onto the one Tree clock.
Body/feed stocks use an explicit 0.1 mass scale relative to original v0.21.7
profile bodies; this is a model interface policy, not a biological conversion.
"""
from __future__ import annotations
from dataclasses import dataclass,field
from collections import Counter
from habitat_bridge import CohortAnimal, HOME, SPECIES, PREY
from habitat_bridge_02114 import HabitatBridge214

MASS_SCALE=.1
YEAR=360
# species: maturity, independence, senescence, max_age, gestation, litter,
# breeding season, parental care, metabolism, intake, baseline hazard,
# body_mass, newborn_mass, birth_cost
PILOT={
 'field_mouse':     (36,12,130,225,12,(2,3),(20,325),True,.065,.22,.0008,.52,.055,.23),
 'meadow_grazer':  (100,35,420,730,27,(1,2),(25,285),True,.090,.32,.00045,1.6,.16,.40),
 'forest_browser': (140,45,560,970,36,(1,2),(15,315),True,.095,.34,.00040,1.9,.20,.46),
 'ridge_hound':    (180,55,690,1100,52,(1,2),(40,295),True,.115,.28,.00035,2.6,.23,.50),
 'carrion_bird':   (105,26,440,750,28,(1,2),(35,310),True,.070,.19,.00040,1.1,.12,.30),
}
# Direct transcriptions of v0.21.7 NeedsTrait fields (except optional capital
# breeding, deliberately disabled): hunger, immediate risk, parental,
# reproductive, exploration, concealment, search, reserve safety margin.
NEEDS={
 'field_mouse':(1.20,1.30,.75,.60,1.0,1.30,.40,1.1),
 'meadow_grazer':(1.20,1.20,1.10,.80,.65,1.10,.35,1.2),
 'forest_browser':(1.20,1.05,1.20,.85,.65,.95,.40,1.15),
 'ridge_hound':(1.50,.65,1.20,1.15,.85,.40,1.55,1.3),
 'carrion_bird':(1.30,.85,.70,.95,1.20,.45,1.50,1.1),
}
COVER={'forest':.64,'grassland':.30,'wetland':.50,'ridge':.34,'floodplain':.46}
assert set(PILOT)==set(SPECIES)==set(NEEDS)

@dataclass(frozen=True)
class LifeProfile:
    maturity:int; independence:int; senescence:int; max_age:int
    gestation:int; litter:tuple[int,int]; breeding:tuple[int,int]; parental:bool
    metabolism:float; intake:float; hazard:float; body:float; newborn:float; birth_cost:float
    def stage(self,age):
        if age<self.independence:return 'dependent'
        if age<self.maturity:return 'juvenile'
        if age<self.senescence:return 'adult'
        return 'elder'
    def adult_mass(self):return self.body*MASS_SCALE
    def newborn_mass(self):return self.newborn*MASS_SCALE
    def maternal_cap(self):return self.birth_cost*MASS_SCALE*5
PROFILES={k:LifeProfile(*v) for k,v in PILOT.items()}

@dataclass
class LifeAnimal(CohortAnimal):
    pregnant_until:int|None=None
    pregnancy_father:str|None=None
    last_birth_day:int=-10000
    caregiver_ids:set[str]=field(default_factory=set)
    parent_ids:tuple[str,...]=()
    condition:float=1.
    hunt_skill:float=.10
    avoid_skill:float=.10
    generation:int=0
    hidden:bool=False
    @property
    def stage(self):return PROFILES[self.species].stage(self.age)

class LifeBookAdapter:
    """Only ownership/physical-account map for one Book, never a second economy.

    Authoritative native WORLD-023 residents remain on their original scheduler.
    No body mass is counted twice, and maternal/gut stocks are individual-owned.
    """
    def __init__(self,bridge):self.bridge=bridge
    @property
    def book(self):return self.bridge.book
    def live(self,a):return f'live:{a.id}'
    def gut(self,a):return f'gut:{a.id}'
    def maternal(self,a):return f'maternal:{a.id}'
    def reserve(self,a):return f'animal:{a.id}'
    def plant(self,a):return self.bridge.tree.acct('plant',a.habitat)
    def detritus(self,a):return self.bridge.tree.acct('detritus',a.habitat)
    def chem(self,a):return self.bridge.tree.acct('chem',a.habitat)
    def convert(self,legs):return self.bridge._convert(legs)
    def birth(self,mom,child,mass):
        if self.book.mass[self.maternal(mom)]+1e-10<mass:return False
        self.convert([(self.maternal(mom),self.live(child),mass)])
        energy=min(.003,self.book.energy[self.reserve(mom)]*.14)
        if energy:self.book.move(energy=[(self.reserve(mom),self.reserve(child),energy)])
        return True
    def clear_corpse(self,a):
        habitat=a.habitat
        destination=(self.bridge.carrion(habitat) if self.bridge.tree.state in ('active','germinating')
                     else f'remnant:tree:{self.bridge.tree.id}:{habitat}')
        for account in (self.live(a),self.maternal(a),self.gut(a)):
            q=self.book.mass[account]
            if q>0:self.convert([(account,destination,q)])
        e=self.book.energy[self.reserve(a)]
        if e>0:self.book.move(energy=[(self.reserve(a),'environment:heat',e)])

class HabitatBridge215(HabitatBridge214):
    """Daily life-history scheduler; old bridge retained for controlled replay."""
    def __init__(self,tree,seed=9711,counts=None):
        self.physical=LifeBookAdapter(self)
        super().__init__(tree,seed=seed,counts=counts)
        self._reproduction_counters=Counter()
        self.needs_last={}
        self.needs_choices=Counter()

    def _initial_age(self,p):
        r=self.rng.random()
        if r<.16:return self.rng.randrange(0,p.independence)
        if r<.37:return self.rng.randrange(p.independence,p.maturity)
        if r<.85:return self.rng.randrange(p.maturity,p.senescence)
        return self.rng.randrange(p.senescence,p.max_age)

    def _new(self,species,habitat,initial=False,parent=None):
        """Only opening snapshot uses habitat source; births use maternal account."""
        if not initial:raise RuntimeError('use maternal-funded _birth for descendants')
        p=PROFILES[species]
        age=self._initial_age(p)
        body=p.adult_mass()*(.35+.65*min(1,age/p.maturity))
        stored=p.birth_cost*MASS_SCALE*.6 if age>=p.maturity else 0.
        plant=self.tree.acct('plant',habitat);chem=self.tree.acct('chem',habitat)
        if self.book.mass[plant]<body+stored or self.book.energy[chem]<.025:return None
        self.serial+=1;uid=f'WTBIO-{self.serial:07d}'
        self._convert([(plant,f'live:{uid}',body)]+([(plant,f'maternal:{uid}',stored)] if stored else []))
        self.book.move(energy=[(chem,f'animal:{uid}',.025)])
        # Alternating sexes prevent artificial zero-mate initial cohorts when >=2.
        sex='F' if self.serial%2 else 'M'
        a=LifeAnimal(uid,species,habitat,sex,age,energy=.025,
                     avoid_skill=.10+min(.3,age/p.max_age*.30),hunt_skill=.10)
        self.actors[uid]=a
        self._log('introduced',actor=uid,species=species,habitat=habitat,stage=a.stage,age=age)
        return a

    def _check_registry(self):
        super()._check_registry()
        for a in self.actors.values():
            if a.alive and a.pregnant_until is not None:
                assert a.sex=='F' and a.pregnancy_father is not None
            if not a.alive:
                assert self.book.mass[self.physical.maternal(a)]<1e-7
                assert self.book.mass[self.physical.gut(a)]<1e-7

    def _death(self,a,cause):
        if not a.alive:return
        self.physical.clear_corpse(a)
        a.alive=False;a.pregnant_until=None;a.pregnancy_father=None
        for other in self.actors.values():other.caregiver_ids.discard(a.id)
        self._log('death',actor=a.id,cause=cause,species=a.species,habitat=a.habitat,age=a.age)

    def _metabolize(self,a):
        p=PROFILES[a.species]
        demand=.001*(.5+.5*p.metabolism/.1)
        available=self.book.energy[self.physical.reserve(a)]
        burn=min(available,demand)
        if burn>0:self.book.move(energy=[(self.physical.reserve(a),'environment:heat',burn)])
        a.condition=min(1.,a.condition+.007) if burn>=.8*demand else max(0.,a.condition-.035)

    def _feed_stock(self,a,source,kind):
        p=PROFILES[a.species];b=self.book;ph=self.physical
        q=min(p.intake*.012,b.mass[source],max(0.,b.energy[ph.chem(a)]/.80))
        if q<.0004:return False
        target=p.adult_mass()*(.35+.65*min(1,a.age/p.maturity))
        growth=min(q*.17,max(0.,target-b.mass[ph.live(a)])) if a.age<p.maturity else 0.
        store=(min(q*.22,max(0.,p.maternal_cap()-b.mass[ph.maternal(a)]))
               if a.sex=='F' and a.stage=='adult' else 0.)
        rest=q-store-growth
        legs=[]
        if growth>1e-12:legs.append((source,ph.live(a),growth))
        if store>1e-12:legs.append((source,ph.maternal(a),store))
        if rest>1e-12:legs.append((source,ph.gut(a),rest))
        if legs:ph.convert(legs)
        en=min(b.energy[ph.chem(a)],q*.80)
        if en>0:b.move(energy=[(ph.chem(a),ph.reserve(a),en)])
        gut=b.mass[ph.gut(a)]
        if gut>1e-12:ph.convert([(ph.gut(a),ph.detritus(a),gut)])
        self._log('feeding',actor=a.id,habitat=a.habitat,food_source=kind,mass=q,
                  maternal_mass=store,growth=growth)
        return True

    def _feed_herbivore(self,a):
        if self.book.mass[self.physical.plant(a)]<=.04:return False
        return self._feed_stock(a,self.physical.plant(a),'plant')

    def _feed_scavenger(self,a):
        site=self.carrion(a.habitat)
        if self.book.mass[site]>.0004:return self._feed_stock(a,site,'carrion')
        # v0.21.7 carrion birds have seed/fruit fallback; synthetic tree only
        # has aggregated plants, so represent it by a lower-rate plant meal.
        if self.book.mass[self.physical.plant(a)]>.04 and self.day%2==0:
            return self._feed_stock(a,self.physical.plant(a),'plant_fallback')
        return False

    def _hunt(self,a):
        if a.species not in PREY:return False
        # Only conspecific prey co-located after funded movement; no omniscient map.
        prey=[x for x in self.actors.values() if x.alive and x.species in PREY[a.species]
              and x.habitat==a.habitat and x.id!=a.id]
        if not prey:return False
        cover=COVER[a.habitat]
        # Perception can fail before an attempted strike. Concealment is a risk
        # reduction, never guaranteed immunity from a predator.
        detectable=[x for x in prey if self.rng.random()<max(.05,.75-cover*.38-(.35 if x.hidden else 0))]
        if not detectable:return False
        victim=self.rng.choice(detectable)
        self._log('hunt_attempt',actor=a.id,prey=victim.id,habitat=a.habitat)
        chance=max(.02,min(.74,.18+.24*a.hunt_skill+
                       .16*(victim.stage=='dependent')-.21*victim.avoid_skill-.08*cover-
                       (.14 if victim.hidden else 0)))
        if self.rng.random()>=chance:
            victim.avoid_skill=min(1.,victim.avoid_skill+.0035)
            self._log('escape',actor=victim.id,predator=a.id,habitat=victim.habitat)
            return False
        m=self.book.mass[self.physical.live(victim)];e=self.book.energy[self.physical.reserve(victim)]
        eat=m*.3
        store=min(eat*.20,max(0.,PROFILES[a.species].maternal_cap()-self.book.mass[self.physical.maternal(a)])) if a.sex=='F' and a.stage=='adult' else 0.
        legs=[(self.physical.live(victim),self.physical.gut(a),eat-store),
              (self.physical.live(victim),self.carrion(a.habitat),m*.7)]
        if store>0:legs.append((self.physical.live(victim),self.physical.maternal(a),store))
        self.physical.convert(legs)
        gut=self.book.mass[self.physical.gut(a)]
        if gut>0:self.physical.convert([(self.physical.gut(a),self.physical.detritus(a),gut)])
        if e>0:self.book.move(energy=[(self.physical.reserve(victim),self.physical.reserve(a),e*.65),
                                     (self.physical.reserve(victim),'environment:heat',e*.35)])
        extra=self.book.mass[self.physical.maternal(victim)]
        if extra>0:self.physical.convert([(self.physical.maternal(victim),self.carrion(a.habitat),extra)])
        oldgut=self.book.mass[self.physical.gut(victim)]
        if oldgut>0:self.physical.convert([(self.physical.gut(victim),self.carrion(a.habitat),oldgut)])
        victim.alive=False;victim.pregnant_until=None;victim.pregnancy_father=None
        for other in self.actors.values():other.caregiver_ids.discard(victim.id)
        a.hunt_skill=min(1.,a.hunt_skill+.0035)
        self._log('death',actor=victim.id,species=victim.species,cause='predation',habitat=victim.habitat)
        self._log('predation',predator=a.id,prey=victim.id,habitat=a.habitat,
                  prey_mass=m,carcass_mass=m*.7)
        return True

    def evaluate_needs(self,a):
        """Adapt v0.21.7 relative-utility decision to immediately local cues.

        A NEED score informs behavior, never creates resources or guarantees
        mating/hiding/survival. Only same-habitat actors are perceived.
        """
        t=NEEDS[a.species]
        reserve=self.book.energy[self.physical.reserve(a)]
        target=.035*t[7]  # scaled energy-reserve target (not a calibrated rate)
        hunger=max(0.,min(1.,(target-reserve)/max(.001,target)))
        danger=(a.species not in PREY and a.species!='carrion_bird' and
                any(x.alive and x.species in PREY and x.habitat==a.habitat
                    for x in self.actors.values()))
        dependents=sum(x.alive and x.stage=='dependent' and a.id in x.caregiver_ids
                       and x.habitat==a.habitat for x in self.actors.values())
        p=PROFILES[a.species]
        mate=(a.sex=='F' and a.stage=='adult' and
              p.breeding[0]<=self.day%YEAR<=p.breeding[1] and
              any(x.id!=a.id and x.alive and x.sex=='M' and x.species==a.species
                  and x.stage=='adult' and x.habitat==a.habitat and x.condition>=.65
                  for x in self.actors.values()))
        scores={
          'feed':t[0]*(.20+1.70*hunger),
          'hide':float(danger)*t[1]*t[5]*(1.-.66*hunger),
          'care':t[2]*(.55+.20*min(2,dependents))*(1-.67*hunger)
                     if dependents and a.stage in ('adult','elder') else 0.,
          'mate':t[3]*(.65+.25*(1-hunger)) if mate and a.condition>=.65 and reserve>=.012 else 0.,
          'explore':t[4]*(.30 if a.stage=='juvenile' else .09)*(1-hunger),
          'rest':(.20 if a.stage=='elder' else .12)*(1-hunger),
        }
        if a.species in PREY or a.species=='carrion_bird':
            scores['search']=t[6]*(.02+1.65*hunger)
            local_food=(any(x.alive and x.species in PREY[a.species]
                            and x.habitat==a.habitat for x in self.actors.values())
                        if a.species in PREY else self.book.mass[self.carrion(a.habitat)]>.0004)
            scores['feed']*=1.15 if local_food else .08
        if danger and hunger<.25:scores['hide']*=1.6
        if hunger>=.82:
            scores['feed']*=1.8
            if 'search' in scores:scores['search']*=1.8
        if a.stage=='dependent':scores={'stay_with_caregiver':1.,'explore':.1}
        action=max(scores,key=scores.__getitem__)
        self.needs_choices[f'{a.species}:{action}']+=1
        if self.needs_last.get(a.id)!=action:
            self._log('need_transition',actor=a.id,action=action,from_action=self.needs_last.get(a.id),
                      hunger=round(hunger,4),threat=bool(danger),dependents=dependents)
            self.needs_last[a.id]=action
        return action,hunger,bool(danger)

    def _migrate(self,a,decision=None):
        here=a.habitat;neighbors=tuple(self.tree.habitats[here].neighbors)
        if not neighbors:return False
        energy=self.physical.reserve(a)
        if self.book.energy[energy]<self.TRAVEL_COST+.0005:return False
        destination=None;reason=None
        if a.species in PREY:
            if decision in ('rest','stay_with_caregiver','mate','care'):return False
            # Only scents in immediately adjacent habitats can trigger a move;
            # existence and abundance elsewhere are not observed.
            cues=[p for p in neighbors if any(x.alive and x.habitat==p and
                  x.species in PREY[a.species] for x in self.actors.values())]
            if cues and self.rng.random()<.60:
                destination=self.rng.choice(cues);reason='adjacent_scent'
            elif self.day%7==0 and self.rng.random()<.60:
                destination=self.rng.choice(neighbors);reason='exploration'
        elif a.species=='carrion_bird':
            near=[p for p in neighbors if self.book.mass[self.carrion(p)]>.012]
            if near and self.rng.random()<.65:
                destination=self.rng.choice(near);reason='adjacent_carrion_scent'
        else:
            danger=any(x.alive and x.species in PREY and x.habitat==here for x in self.actors.values())
            trait=NEEDS[a.species]
            hunger=max(0,1-self.book.energy[energy]/(.035*trait[7]))
            conceal=max(0,min(.90,COVER[here]*trait[5]*(1-hunger)))
            a.hidden=danger and decision=='hide' and self.rng.random()<conceal
            if danger and not a.hidden and self.rng.random()<(.18+.20*a.avoid_skill):
                destination=self.rng.choice(neighbors);reason='predator_avoidance'
            elif decision in ('feed','explore') and self.book.mass[self.physical.plant(a)]<.22 and self.day%3==0:
                destination=self.rng.choice(neighbors);reason='forage_search'
        if destination is None:return False
        self.book.move(energy=[(energy,'environment:heat',self.TRAVEL_COST)])
        a.habitat=destination;a.hidden=False
        self._log('migration',actor=a.id,species=a.species,from_habitat=here,
                  to_habitat=destination,reason=reason,energy_cost=self.TRAVEL_COST)
        return True

    def _care(self,a,episode="primary"):
        if a.stage not in ('adult','elder'):return
        children=[x for x in self.actors.values() if x.alive and x.stage=='dependent' and
                  a.id in x.caregiver_ids and x.habitat==a.habitat]
        for child in children:
            e=self.book.energy[self.physical.reserve(a)]
            gift=min(.0006,max(0.,e-.004))
            if gift>0:
                self.book.move(energy=[(self.physical.reserve(a),self.physical.reserve(child),gift)])
                self._log('parental_care',actor=a.id,child=child.id,energy=gift,episode=episode)

    def _reproduce(self):
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
            if self.rng.random()>=.042:continue
            father=self.rng.choice(mates)
            mom.pregnancy_father=father.id;mom.pregnant_until=self.day+p.gestation
            self._log('conception',mother=mom.id,father=father.id,due=mom.pregnant_until,
                      species=mom.species,maternal_stock=self.book.mass[self.physical.maternal(mom)])

    def _birth(self,mom):
        p=PROFILES[mom.species]
        if not mom.alive or mom.pregnant_until is None or self.day<mom.pregnant_until:return 0
        mom.pregnant_until=None
        n=min(self.rng.randint(*p.litter),int((self.book.mass[self.physical.maternal(mom)]+1e-10)/p.newborn_mass()))
        if n<=0:
            self._log('failed_birth',mother=mom.id,cause='maternal_stock');mom.pregnancy_father=None
            return 0
        if sum(a.alive for a in self.actors.values())+n>2500:
            raise OverflowError('population safety guard: abort rather than silently omit births')
        father=mom.pregnancy_father
        for _ in range(n):
            self.serial+=1;uid=f'WTBIO-{self.serial:07d}'
            child=LifeAnimal(id=uid,species=mom.species,habitat=mom.habitat,
                             sex='F' if self.rng.random()<.5 else 'M',age=0,
                             parent=mom.id,parent_ids=(mom.id,father) if father else (mom.id,),
                             caregiver_ids={mom.id} if p.parental else set(),
                             generation=mom.generation+1)
            if not self.physical.birth(mom,child,p.newborn_mass()):
                raise AssertionError('funded maternal birth failed')
            self.actors[uid]=child
            self._log('birth',actor=uid,mother=mom.id,father=father,species=mom.species,
                      habitat=mom.habitat,mass=p.newborn_mass(),generation=child.generation)
        mom.last_birth_day=self.day;mom.pregnancy_father=None
        return n

    def step(self,tick):
        if tick!=self.day+1:raise AssertionError('life-history clock mismatch')
        self.day=tick
        if self.tree.state not in ('active','germinating'):
            for a in list(self.actors.values()):
                if a.alive:self._death(a,'world_tree_collapse')
            for habitat in self.tree.habitats:
                q=self.book.mass[self.carrion(habitat)]
                if q>0:self.physical.convert([(self.carrion(habitat),f'remnant:tree:{self.tree.id}:{habitat}',q)])
            self.book.audit();self._check_registry();return
        for a in list(self.actors.values()):
            if not a.alive:continue
            a.age+=1
            self._metabolize(a)
            action,hunger,_=self.evaluate_needs(a)
            self._migrate(a,action)
            if a.species in PREY:
                if action in ('feed','search'):self._hunt(a)
            elif a.species=='carrion_bird':
                if action in ('feed','search'):self._feed_scavenger(a)
            elif a.stage!='dependent':
                if action=='feed' or hunger>.55 or (action=='hide' and hunger>.35):
                    self._feed_herbivore(a)
            if a.stage in ('adult','elder'):
                if action=='care':self._care(a,episode='primary')
                # One bounded second opportunity per day, even after another action.
                # Not guaranteed: local dependents, available reserves and a stochastic
                # caregiving decision are all required. No minting or forced survival.
                elif self.rng.random()<.65:
                    self._care(a,episode='secondary')
            if self.book.energy[self.physical.reserve(a)]<.0005 or a.condition<=0 or a.age>=PROFILES[a.species].max_age:
                self._death(a,'starvation' if a.condition<=0 or self.book.energy[self.physical.reserve(a)]<.0005 else 'age')
            elif self.rng.random()<PROFILES[a.species].hazard * (3 if a.stage=='elder' else 1):
                self._death(a,'baseline_mortality')
        self._reproduce();self._decay()
        self.book.audit();self._check_registry()

    def census(self):
        output=super().census()
        output['conceptions']=self.stats['conception']
        output['births']=self.stats['birth']
        output['dependents']=sum(a.alive and a.stage=='dependent' for a in self.actors.values())
        output['pregnancies']=sum(a.alive and a.pregnant_until is not None for a in self.actors.values())
        output['need_choices']=dict(self.needs_choices)
        output['maternal_mass']=round(sum(self.book.mass[self.physical.maternal(a)] for a in self.actors.values()),9)
        return output
