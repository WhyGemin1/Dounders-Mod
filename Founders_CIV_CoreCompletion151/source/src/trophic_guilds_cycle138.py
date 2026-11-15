"""Cycle138-G opt-in trophic diversification on the ONE Cycle135 World Tree Book.

All new animals share the existing bridge scheduler and the native WORLD-023 Book;
no births, feed, ant brood or megaherbivore modifications may create mass/energy.
Eight added model roles, with parameters deliberately NOT empirical calibrations:
  burrow_rabbit, field_vole, ant_colony, insectivore_shrew,
  red_fox, golden_jackal, forest_elephant, woolly_mammoth (eight roles).
Ant 'individual' is a QUEEN-LED COLONY actor; workers are pooled live biomass.
This is a synthetic mechanistic test, not faithful per-species biogeography.

The original five-species baseline and A000-A111 factorial remain untouched.
G=True is a separately controlled additional treatment; compare only paired seeds.
"""
from __future__ import annotations
from collections import Counter
from contextlib import contextmanager

from eco_factorial_cycle138 import EcoBridge138, UnifiedEcoFactorial138
from habitat_bridge import PREY, SPECIES
from species_life_02115 import LifeAnimal, LifeProfile, PROFILES, NEEDS, MASS_SCALE
from tissue_energy_02120 import fund_tissue

# Same 14-parameter schema as the existing life-history adapter. Age units days;
# body units are *synthetic* original body numbers later multiplied by MASS_SCALE.
# Adult megafauna do not mature on a 1,080-day window; don't infer extinction
# from a lack of their second generation during that horizon.
GUILD_PROFILE_VALUES={
 'burrow_rabbit': (120,25,1250,2700,30,(3,6),(30,310),True,.073,.30,.00065,1.2,.12,.90),
 'field_vole': (48,15,290,460,21,(2,5),(20,325),True,.061,.18,.00095,.45,.052,.30),
 'ant_colony': (150,0,1750,3200,60,(1,1),(80,230),False,.048,.10,.00016,.48,.16,.26),
 'insectivore_shrew': (65,19,300,460,24,(2,4),(35,300),True,.100,.22,.00085,.48,.050,.30),
 'red_fox': (220,65,1400,2700,51,(1,3),(25,270),True,.103,.34,.00032,2.2,.21,.52),
 'golden_jackal': (240,74,1600,3000,63,(1,3),(30,290),True,.108,.39,.00030,2.7,.25,.58),
 'forest_elephant': (3650,730,12200,22000,650,(1,1),(1,359),True,.100,.92,.00007,18.0,1.80,7.0),
 'woolly_mammoth': (3650,850,12200,22000,660,(1,1),(1,359),True,.108,1.00,.00007,22.0,2.10,8.0),
}
GUILD_NEEDS={
 'burrow_rabbit': (1.30,1.30,.90,.90,.65,1.45,.60,1.10),
 'field_vole': (1.40,1.25,.85,1.,.80,1.20,.70,1.07),
 'ant_colony': (1.30,1.10,1.,.50,.05,1.,.20,.94),
 'insectivore_shrew': (1.70,1.40,1.,.75,.75,.80,1.60,1.20),
 'red_fox': (1.50,.75,1.15,1.0,1.05,.50,1.55,1.23),
 'golden_jackal': (1.45,.72,1.25,1.0,1.10,.50,1.55,1.20),
 'forest_elephant': (1.40,1.15,1.40,.50,.40,.85,.60,1.25),
 'woolly_mammoth': (1.50,1.10,1.40,.50,.40,.75,.60,1.30),
}
GUILD_HOMES={
 'burrow_rabbit':('grassland','forest','floodplain','grassland'),
 'field_vole':('grassland','wetland','grassland','floodplain'),
 'ant_colony':('forest','wetland'),
 'insectivore_shrew':('forest','wetland'),
 'red_fox':('forest','forest'),
 'golden_jackal':('grassland','wetland'),
 'forest_elephant':('forest',),
 'woolly_mammoth':('ridge',),
}
GUILD_FOUNDERS={
 'burrow_rabbit':8,'field_vole':8,'ant_colony':2,
 'insectivore_shrew':4,'red_fox':2,'golden_jackal':2,
 'forest_elephant':1,'woolly_mammoth':1,
}
ALLOWED_HABITATS={
 'burrow_rabbit':('grassland','forest','floodplain'),
 'field_vole':('grassland','floodplain','wetland'),
 'ant_colony':('forest','grassland','floodplain','wetland'),
 'insectivore_shrew':('forest','wetland','floodplain'),
 'red_fox':('forest','grassland','floodplain','ridge'),
 'golden_jackal':('grassland','floodplain','wetland','ridge'),
 'forest_elephant':('forest','wetland','floodplain'),
 'woolly_mammoth':('grassland','ridge'),
}
# Adult megaherbivores intentionally excluded from hunting menus. A predator
# gets rabbit/vole/canid prey, and young megaherbivores are NOT free food.
GUILD_PREDATORS={
 'ridge_hound':('field_mouse','meadow_grazer','burrow_rabbit','field_vole',
                'red_fox','golden_jackal','insectivore_shrew'),
 'red_fox':('field_mouse','field_vole','burrow_rabbit','insectivore_shrew'),
 'golden_jackal':('field_mouse','field_vole','burrow_rabbit','insectivore_shrew'),
 'insectivore_shrew':('ant_colony',),
}
MEGA=('forest_elephant','woolly_mammoth')
CANIDS=('red_fox','golden_jackal')
ANTS='ant_colony'
MIN_QUEEN_MASS=.006
ANT_WORKER_MASS=.00012

# A profile registration is vocabulary only: no base cohorts, prior prey menus,
# RNG state, settings, or source files are changed. The schema is old-vocab-safe.
for _name,_row in GUILD_PROFILE_VALUES.items():
    PROFILES.setdefault(_name,LifeProfile(*_row))
    NEEDS.setdefault(_name,GUILD_NEEDS[_name])

@contextmanager
def _temporary_diet_registry():
    """Legacy life-history routing consults this dict directly.

    Limit its scope to one bridge.step (sequential single-process runs only).
    A parallel worker must run in a different PROCESS, never a thread.
    """
    old={k:PREY.get(k) for k in GUILD_PREDATORS}
    try:
        PREY.update(GUILD_PREDATORS)
        yield
    finally:
        for k,val in old.items():
            if val is None:PREY.pop(k,None)
            else:PREY[k]=val

class GuildBridge138(EcoBridge138):
    def activate_guilds(self,counts=None):
        self.guild_metrics=Counter()
        self.guild_initial_counts=dict(GUILD_FOUNDERS if counts is None else counts)
        for species,n in self.guild_initial_counts.items():
            if species not in GUILD_PROFILE_VALUES or not isinstance(n,int) or n<0:
                raise ValueError('invalid guild species or count')
            for i in range(n):
                actor=self._add_guild_initial(species,i)
                if actor is None:
                    raise RuntimeError('insufficient REAL plant and chemical stocks for initial '+species)
        self.sync_positions()
        self._check_registry()
        self.book.audit()

    def _add_guild_initial(self,species,i):
        p=PROFILES[species];hab=GUILD_HOMES[species][i%len(GUILD_HOMES[species])]
        # Only ant queens (one colony per agent) are all female, not individual workers.
        sex='F' if species==ANTS or i%2==0 else 'M'
        if species in MEGA:age=p.maturity+350+i*15
        elif species==ANTS:age=p.maturity+70+i*3
        else:age=p.maturity+max(2,(p.senescence-p.maturity)//5)+(i%4)*3
        body=p.adult_mass();stored=0. if species==ANTS else (p.birth_cost*MASS_SCALE*.6 if sex=='F' else 0.)
        plant=self.tree.acct('plant',hab);chem=self.tree.acct('chem',hab)
        if self.book.mass[plant]<body+stored or self.book.energy[chem]<.025:return None
        self.serial+=1;uid=f'WTBIO-{self.serial:07d}'
        material=[(plant,f'live:{uid}',body)]
        if stored:material.append((plant,f'maternal:{uid}',stored))
        self.physical.convert(material)
        self.book.move(energy=[(chem,f'animal:{uid}',.025)])
        # The ancestral digestion engine requires funded EMBODIED tissue-energy
        # accounts for every edible animal. Without these, novel prey would
        # yield mass but no nutritional tissue energy to a successful predator.
        for key,mass in ((f'tissue_energy:{uid}',body),
                         (f'maternal_energy:{uid}',stored)):
            amount=min(mass*.06,max(0.,self.book.energy[chem]-.001))
            if amount>1e-12:fund_tissue(self.book,chem,key,amount)
        a=LifeAnimal(id=uid,species=species,habitat=hab,sex=sex,age=age,
             energy=.025,avoid_skill=.12,hunt_skill=.10)
        self.actors[uid]=a
        self.guild_metrics['funded_founders']+=1
        self._log('guild_introduction',actor=uid,species=species,habitat=hab,body=body)
        return a

    def _migrate(self,a,decision=None):
        if a.species==ANTS:return False
        if a.species in MEGA:
            # The chosen physical site must belong to the species' climate/niche.
            if decision not in ('feed','search','explore'):return False
            if self.day%9:return False
            neighbors=[h for h in self.tree.habitats[a.habitat].neighbors
                       if h in ALLOWED_HABITATS[a.species]]
            if not neighbors:return False
            destination=max(neighbors,key=lambda h:self.book.mass[self.tree.acct('plant',h)])
            source=self.physical.reserve(a)
            if self.book.energy[source]<self.TRAVEL_COST+.0005:return False
            self.book.move(energy=[(source,'environment:heat',self.TRAVEL_COST)])
            prior=a.habitat;a.habitat=destination
            self.sync_positions()
            self.guild_metrics['megaherbivore_migrations']+=1
            self._log('migration',actor=a.id,species=a.species,
                      from_habitat=prior,to_habitat=destination,
                      reason='adjacent_niche_forage',energy_cost=self.TRAVEL_COST)
            return True
        return super()._migrate(a,decision)

    def _feed_herbivore(self,a):
        if a.species==ANTS:
            # Ant colonies may forage on existing plant-derived organic matter.
            det=self.tree.acct('detritus',a.habitat)
            if self.book.mass[det]>.005:return self._feed_stock(a,det,'ant_detritus')
        return super()._feed_herbivore(a)

    def _care(self,a,episode='primary'):
        if a.species not in CANIDS:return super()._care(a,episode=episode)
        # Use the established transfer-only parental support, but canids must
        # provision edible CARRION, not a free plant meal. Only J-enabled runs
        # add the second physical meal; preserve all-off main experiment.
        result=super(EcoBridge138,self)._care(a,episode=episode)
        if not self.eco_flags.juvenile or a.stage not in ('adult','elder'):return result
        source=self.carrion(a.habitat)
        for child in tuple(self.actors.values()):
            if not (child.alive and child.stage=='dependent' and
                    a.id in child.caregiver_ids and child.habitat==a.habitat):continue
            if self._child_fed_day.get(child.id)==self.day:continue
            if self.eco_flags.spatial and self._pos(child)!=self._pos(a):continue
            donor=self.physical.reserve(a)
            if self.book.energy[donor]<.008+.00012+.00018:continue
            if self._local_access(a,source)<.0004:continue
            if not self._feed_stock(child,source,'canid_caregiver_carrion'):continue
            self.book.move(energy=[(donor,'environment:heat',.00012),
                                   (donor,self.physical.reserve(child),.00018)])
            self._child_fed_day[child.id]=self.day
            self.eco_metrics['caregiver_meals']+=1
            self.guild_metrics['canid_dependent_provisions']+=1
            self._log('caregiver_meal',actor=a.id,child=child.id,
                      food_source=source,work=.00012,energy=.00018)
        return result

    def _hunt(self,a):
        if a.species=='insectivore_shrew':
            if self._ant_worker_take(a):return True
            # Shrews also feed on carrion where it exists.
            return self._optional_scavenge(a)
        result=super()._hunt(a)
        if not result and a.species in CANIDS:
            return self._optional_scavenge(a)
        return result

    def _optional_scavenge(self,a):
        site=self.carrion(a.habitat)
        if self.book.mass[site]<.001:return False
        return self._feed_stock(a,site,'opportunistic_scavenge')

    def _ant_worker_take(self,shrew):
        colonies=[x for x in self.actors.values() if x.alive and x.species==ANTS
                  and x.habitat==shrew.habitat
                  and (not self.eco_flags.spatial or
                       sum(abs(self._pos(shrew)[i]-self._pos(x)[i]) for i in (1,2))<=1)]
        if not colonies:return False
        colony=max(colonies,key=lambda x:self.book.mass[self.physical.live(x)])
        source=self.physical.live(colony)
        available=self.book.mass[source]-MIN_QUEEN_MASS
        q=min(.0015,max(0.,available))
        if q<.0004:return False
        tissue=self.physical.tissue(colony)
        # Energy is taken only from ACTUAL embodied worker energy, and a
        # fraction dissipates; no second meal is minted from habitat chemistry.
        initial_mass=self.book.mass[source]
        energy=min(self.book.energy[tissue],self.book.energy[tissue]*q/max(initial_mass,1e-12))
        self.physical.convert([(source,self.physical.gut(shrew),q)])
        self.physical.convert([(self.physical.gut(shrew),self.physical.detritus(shrew),q)])
        if energy>1e-12:
            gain=energy*.55
            self.book.move(energy=[(tissue,self.physical.reserve(shrew),gain),
                                   (tissue,'environment:heat',energy-gain)])
        self.guild_metrics['ant_worker_mass_eaten']+=q
        self.guild_metrics['ant_worker_foraging_events']+=1
        self._log('ant_worker_foraging',predator=shrew.id,colony=colony.id,
                  consumed_worker_mass=q,energy=energy)
        return True

    def _ant_brood(self,a):
        # Fast worker recruitment is NOT the establishment of daughter colonies.
        # Detritus becomes bounded worker tissue + mineralized soil; every gram
        # and energy increment is debited from a real Book source.
        if self.day%6:return
        body=self.physical.live(a)
        if self.book.mass[body]>=.12:return
        det=self.tree.acct('detritus',a.habitat);chem=self.physical.chem(a)
        sun=self.tree.acct('sun',a.habitat)
        q=min(.0020,max(0.,.12-self.book.mass[body])/.35,self.book.mass[det])
        if q<.0001 or self.book.energy[chem]<q*.4 or self.book.energy[sun]<q*.05:return
        self.physical.convert([(det,body,q*.35),
                               (det,self.tree.acct('soil',a.habitat),q*.65)])
        energy=q*.4
        self.book.move(energy=[(chem,self.physical.tissue(a),energy*.45),
                               (chem,self.physical.reserve(a),energy*.15),
                               (chem,'environment:heat',energy*.40)])
        self.guild_metrics['new_worker_biomass']+=q*.35
        self.guild_metrics['ant_nutrient_mineralization']+=q*.65
        self.guild_metrics['brood_episodes']+=1
        self._log('ant_brood',colony=a.id,new_worker_mass=q*.35,
                  nutrient_to_soil=q*.65)

    def _ant_daughter_colony(self,a):
        # Rare, Book-funded colony founding with a viable queen/worker propagule.
        # Requires physical surplus; unlike worker production it creates a new
        # independent ACTOR. Not guaranteed by time alone.
        if self.day%360 not in (110,111,112):return
        if a.age<PROFILES[ANTS].maturity+120:return
        count=sum(x.alive and x.species==ANTS and x.habitat==a.habitat
                  for x in self.actors.values())
        if count>=12:return
        if self.book.mass[self.physical.live(a)]<.082:return
        if self.book.energy[self.physical.reserve(a)]<.024:return
        if self.rng.random()>=.07:return
        self.serial+=1;uid=f'WTBIO-{self.serial:07d}'
        mass=.024;energy=.010
        self.physical.convert([(self.physical.live(a),f'live:{uid}',mass)])
        self.book.move(energy=[(self.physical.reserve(a),f'animal:{uid}',energy)])
        tissue=self.physical.tissue(a)
        moved_tissue=min(self.book.energy[tissue],
                         self.book.energy[tissue]*mass/max(self.book.mass[self.physical.live(a)]+mass,1e-12))
        if moved_tissue>1e-12:
            self.book.move(energy=[(tissue,f'tissue_energy:{uid}',moved_tissue)])
        daughter=LifeAnimal(id=uid,species=ANTS,habitat=a.habitat,sex='F',age=0,
             parent=a.id,parent_ids=(a.id,),generation=a.generation+1,
             energy=energy,avoid_skill=.10)
        self.actors[uid]=daughter
        self.positions[uid]=self._pos(a)
        self.guild_metrics['daughter_colonies']+=1
        self._log('birth',actor=uid,mother=a.id,species=ANTS,
                  habitat=a.habitat,mass=mass,generation=daughter.generation,
                  reason='funded_colony_budding')

    def _megaherbivore_turnover(self,a):
        # Two possible ecological effects, neither a fixed stability bonus:
        # browsing/trampling removes plants, while some detritus mineralizes.
        # Soil transfer is conditional on existing detritus, and metabolism pays
        # the work. Future versions need plant functional groups/seed dispersal.
        if self.day%5:return
        source=self.physical.reserve(a)
        if self.book.energy[source]<.006:return
        tree=self.tree;h=a.habitat
        plant=tree.acct('plant',h);det=tree.acct('detritus',h);soil=tree.acct('soil',h)
        trample=min(.0025,self.book.mass[plant]*.0008)
        if trample>=.00001:
            self.book.transform([(plant,det,trample)],source=source,work=.00007,
                 energy_outputs=[(source,'environment:heat',.000063)])
            self.guild_metrics['trampled_plant_mass']+=trample
            self._log('megaherbivore_trampling',actor=a.id,mass=trample,habitat=h)
        mineral=min(.0013,self.book.mass[det]*.0006)
        if mineral>=.00001 and self.book.energy[source]>.005:
            self.book.transform([(det,soil,mineral)],source=source,work=.00004,
                 energy_outputs=[(source,'environment:heat',.000036)])
            self.guild_metrics['megaherbivore_mineralization']+=mineral
            self._log('megaherbivore_nutrient_return',actor=a.id,mass=mineral,habitat=h)

    def step(self,tick):
        # Exactly the existing life-history scheduler, with the diet routing
        # locally adjusted during this same step and never left globally dirty.
        with _temporary_diet_registry():
            result=super().step(tick)
            if self.tree.state in ('active','germinating'):
                for a in tuple(self.actors.values()):
                    if not a.alive:continue
                    if a.species==ANTS:
                        self._ant_brood(a)
                        self._ant_daughter_colony(a)
                    elif a.species in MEGA:
                        self._megaherbivore_turnover(a)
            self.sync_positions()
            self.book.audit();self._check_registry()
            return result

    def report(self):
        out=super().report()
        out.update({s:sum(x.alive and x.species==s for x in self.actors.values())
                    for s in GUILD_PROFILE_VALUES})
        return out

    def guild_summary(self):
        self.sync_positions()
        return {'metrics':dict(self.guild_metrics),
          'by_species':{s:sum(x.alive and x.species==s for x in self.actors.values())
                        for s in GUILD_PROFILE_VALUES},
          'ant_colony_workers_approx':sum(max(0,int((self.book.mass[self.physical.live(x)]-
                   MIN_QUEEN_MASS)/ANT_WORKER_MASS)) for x in self.actors.values()
                  if x.alive and x.species==ANTS),
          'total_actors':len(self.actors)}

class UnifiedTrophicGuild138(UnifiedEcoFactorial138):
    def __init__(self,seed=9711,*,expanded_food_web=False,guild_counts=None,**kwargs):
        if type(expanded_food_web) is not bool:raise TypeError('expanded_food_web must be bool')
        super().__init__(seed=seed,**kwargs)
        self.expanded_food_web=expanded_food_web
        if expanded_food_web:
            if not isinstance(self.bridge,EcoBridge138):raise TypeError('guild bridge base mismatch')
            self.bridge.__class__=GuildBridge138
            self.bridge.activate_guilds(guild_counts)
            assert self.host.book is self.bridge.book is self.bridge.tree.book
            self._check()
    def report(self):
        out=super().report()
        out['expanded_food_web']=self.expanded_food_web
        if self.expanded_food_web:out['guilds']=self.bridge.guild_summary()
        return out
