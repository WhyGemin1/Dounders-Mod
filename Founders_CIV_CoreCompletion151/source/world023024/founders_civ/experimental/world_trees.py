"""WORLD-023A/B experimental vertical slice: a physically-accounted living World Tree.

One shared v0.18 Book. No direct mutation of ledger balances after freeze.
All numbers are uncalibrated *synthetic* ecological coefficients. A tick is one
abstract ecological day, not a generation. No human-consciousness claims.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from random import Random
from typing import Optional

from .social_agents import stable_seed
from knowledge_architecture import Claim, encounter

BIOMES = ('forest', 'grassland', 'wetland', 'ridge')
NEIGHBORS = {'forest': ('grassland', 'wetland'),
             'grassland': ('forest', 'ridge'),
             'wetland': ('forest', 'ridge'),
             'ridge': ('grassland', 'wetland')}
# Transfers from existing Solara patches into one new tree. No seeding after freeze.
START = {'soil': 18., 'plant': 7.5, 'detritus': 2., 'water': 22.}
START_CHEM = 3.0
START_SUN = .7
INITIAL_RESIDENTS_PER_HABITAT = 4


@dataclass
class TreeResident:
    id: str
    world: str
    habitat: str
    age: int
    born_tick: int
    max_age: int
    parent: Optional[str] = None
    last_birth: int = -20
    alive: bool = True
    health: float = 1.0
    generation: int = 0
    # Migration history belongs to the resident; checkpoint serializers keep it.
    last_migration_age: int = -99999
    last_migration_origin: Optional[str] = None


@dataclass
class Habitat:
    biome: str
    neighbors: tuple[str, ...]
    sunlight: float = 0.0
    moisture: float = 0.0
    season: str = 'wet'


class WorldTree:
    """One world enclosed by a planted World Tree. Actor/ledger identity is unique."""
    def __init__(self, sim, creation, blueprint):
        self.sim = sim
        self.book = sim.book
        self.id = creation['id']
        self.realm_id = creation['parent']
        self.owner = creation['owner']
        self.seed_id = blueprint.id
        self.rules = dict(blueprint.rules)  # Approved seed snapshot, not live edit.
        self.state = 'germinating'
        self.age = 0
        self.habitats = {k: Habitat(k, NEIGHBORS[k]) for k in BIOMES}
        self.residents: dict[str, TreeResident] = {}
        self.serial = 0
        self.counters = Counter()
        # Experimental policy knob. 0 replays the v0.21.17 movement policy;
        # 6 days introduces migration friction without injecting any resources.
        # Control is the default until multi-seed lifecycle validation succeeds.
        self.migration_cooldown_days = 0
        self.timeline = []
        self.observations = {}
        self.research = {}
        self.species_seed_ids = []
        self.species_rules = {}
        self.last_txn = None
        self.claim_id=f'world_ecology:{self.id}'
        self.sim.knowledge.add(Claim(self.claim_id,f'world_tree_ecology:{self.id}',
             'Patterns of resources, population, seasonal change and mortality in the living World Tree',kind='observation'))
        self.daily_events=[]
        self.provisioning=None  # Optional C003 experimental arm; baseline remains intact.
        self._populate()

    @staticmethod
    def preflight(book):
        """Call BEFORE planting; all source amounts required for an initial tree."""
        for p in BIOMES:
            for typ, amount in START.items():
                if book.mass[f'{typ}:Solara:{p}'] + 1e-8 < amount:
                    raise ValueError(f'World Tree initial {typ} unavailable in Solara:{p}')
            if book.energy[f'chem:Solara:{p}'] + 1e-8 < START_CHEM:
                raise ValueError('World Tree biochemical energy unavailable')
        if book.energy['house'] < 4 * START_SUN:
            raise ValueError('World Tree initial sunlight energy unavailable')

    def acct(self,typ,biome):
        return f'{typ}:tree:{self.id}:{biome}'

    def _event(self, action, actor=None, txn=None, decision_parent=None, **kw):
        self.counters[action] += 1
        return self.sim.log(action, actor if actor is not None else f'WORLD:{self.id}', parent=decision_parent, txn=txn, creation=self.id,
                            habitat=kw.pop('habitat', None), **kw)

    def _populate(self):
        """Move existing matter and energy to local habitat accounts, then fund individuals."""
        self.preflight(self.book)
        legs=[];en=[]
        for p in BIOMES:
            for typ,amt in START.items():
                legs.append((f'{typ}:Solara:{p}',self.acct(typ,p),amt))
            en.append((f'chem:Solara:{p}',self.acct('chem',p),START_CHEM))
            en.append(('house',self.acct('sun',p),START_SUN))
        self.book.move(material=legs,energy=en)
        self.book.move(material=[(self.acct('water',p),f'water:tree:{self.id}:cloud',1.) for p in BIOMES])
        # A world by itself is unpopulated. A separately researched Species
        # Seed must be approved and planted before mortal residents appear.
        self._event('tree_germinated',habitats=len(self.habitats),residents=len(self.residents),
                    blueprint=self.seed_id,realm=self.realm_id)
        self._snapshot()

    def preflight_species(self):
        if self.state=='archived' or self.species_seed_ids:
            raise ValueError('Species Seed not eligible for introduction')
        for p in BIOMES:
            n=INITIAL_RESIDENTS_PER_HABITAT
            if (self.book.mass[self.acct('plant',p)]+1e-9<n*(.11+.19) or
                self.book.energy[self.acct('sun',p)]+1e-9<n*.018 or
                self.book.energy[self.acct('chem',p)]+1e-9<n*.045):
                raise ValueError(f'Species Seed lacks living habitat resources: {p}')

    def admit_species(self, species_creation, species_blueprint):
        if self.state=='archived':raise ValueError('world collapsed')
        if self.species_seed_ids:raise ValueError('pilot supports one starter Species Seed per tree')
        self.preflight_species()
        if species_creation['parent']!=self.id:raise ValueError('Species Seed not hosted by World Tree')
        # The independently reviewed Species Seed is retained as the provenance
        # for the founding population. Its numeric rules are experimental.
        self.species_rules=dict(species_blueprint.rules)
        self.species_seed_ids.append(species_creation['id'])
        for p in BIOMES:
            for i in range(INITIAL_RESIDENTS_PER_HABITAT):
                self._new_resident(p,parent=None,initial=True,index=i)
        self.state='active'
        self.sim.seeds.plants[self.id]['inhabitants']=self.population
        self._event('tree_species_introduced',seed=species_blueprint.id,
                    species_creation=species_creation['id'],founder=species_blueprint.author,
                    initial_population=self.population)
        self._snapshot()

    def _new_resident(self, biome, parent=None, initial=False, index=0):
        if parent is None and not initial:raise ValueError('non-initial births need a parent')
        self.serial += 1
        aid=f'{self.id}:R{self.serial:05d}'
        if aid in self.residents:raise ValueError('duplicate resident id')
        if initial:
            # World is initially populated by a provisional founder-approved starter
            # population; provenance is the seed, not spontaneous reproduction.
            self.book.transform([(self.acct('plant',biome),f'body:{aid}',.11),
                                 (self.acct('plant',biome),f'fuel:{aid}',.19)],
                                source=self.acct('sun',biome),work=.018,
                                energy_outputs=[(self.acct('sun',biome),self.acct('heat',biome),.0162)])
            self.book.move(energy=[(self.acct('chem',biome),f'metabolic:{aid}',.045)])
            age=5+index*3
            generation=0
        else:
            # Birth draws physical biomass and stored energy from the parent.
            # The parent's fuel becomes child's body (funded state change) and
            # child's fuel (same stock class, ownership transfer).
            self.book.transform([(f'fuel:{parent.id}',f'body:{aid}',.095)],
                                source=f'metabolic:{parent.id}',work=.011,
                                energy_outputs=[(f'metabolic:{parent.id}',self.acct('heat',biome),.0099)])
            self.book.move(material=[(f'fuel:{parent.id}',f'fuel:{aid}',.050)],
                           energy=[(f'metabolic:{parent.id}',f'metabolic:{aid}',.012)])
            age=0
            generation=parent.generation+1
            parent.last_birth=self.age
            self._event('tree_birth',actor=parent.id,habitat=biome,child=aid,
                        generation=generation,parent_resident=parent.id)
        r=TreeResident(id=aid,world=self.id,habitat=biome,age=age,born_tick=self.age,
                       max_age=int(62+25*self.species_rules.get('lifespan',.65))+(stable_seed(self.sim.seed,aid,'lifespan')%24),
                       parent=parent.id if parent else None,generation=generation)
        self.residents[aid]=r
        self.sim.seeds.constructs.items[self.id].inhabitants.add(aid)
        return r

    def _material_change(self,typ_from,typ_to,place,q,energy_source,work_factor=.04):
        if q<=0:return None
        work=q*work_factor
        if self.book.energy[energy_source]+1e-10 < work:return None
        return self.book.transform([(self.acct(typ_from,place),self.acct(typ_to,place),q)],
                                   source=energy_source,work=work,
                                   energy_outputs=[(energy_source,self.acct('heat',place),.9*work)])

    def _climate_and_plants(self):
        # Two 20-day seasons; wet-season input varies with approved seed parameters.
        wet = ((self.age-1)//20)%2 == 0
        cloud=f'water:tree:{self.id}:cloud'
        rain_factor = (.36 if wet else .055)*(.7+.6*self.rules['moisture'])*getattr(self,'precipitation_factor',1.0)
        for p,h in self.habitats.items():
            h.season='wet' if wet else 'dry'
            sun_req=(.35 if wet else .26)*(.70+.60*self.rules['daylight'])
            charge=min(sun_req,self.book.energy['house'])
            if charge>0:
                self.book.move(energy=[('house',self.acct('sun',p),charge)])
            # Water changes account/location, not type. 'cloud' is a bookkeeping
            # reservoir for circulation, not a detailed phase-change simulation.
            q=min(self.book.mass[self.acct('water',p)],.19 if wet else .29)
            if q>0:self.book.move(material=[(self.acct('water',p),cloud,q)])
            rainfall=min(self.book.mass[cloud],rain_factor*(.85 if p=='ridge' else 1.0))
            if rainfall>0:self.book.move(material=[(cloud,self.acct('water',p),rainfall)])
            h.moisture=self.book.mass[self.acct('water',p)]
            h.sunlight=self.book.energy[self.acct('sun',p)]
            sun=self.acct('sun',p)
            # Decomposers return detritus to available substrate, funded by sunlight.
            det=self.book.mass[self.acct('detritus',p)]
            reclaim=min(det*.12,.23)
            self._material_change('detritus','soil',p,reclaim,sun,.025)
            # Turnover moves plant biomass to detritus, leaving reversible nutrients.
            plant=self.book.mass[self.acct('plant',p)]
            litter=min(plant*.0045,.06)
            self._material_change('plant','detritus',p,litter,sun,.025)
            rate=(.23 if wet else .14)*(.65+.65*self.rules['recycling'])
            growth=min(rate,self.book.mass[self.acct('soil',p)]*.03,
                       self.book.mass[self.acct('water',p)]*.04,
                       self.book.energy[sun]/.30)
            if growth>1e-9:
                work=growth*.30
                txn=self.book.transform([(self.acct('soil',p),self.acct('plant',p),growth)],
                    source=sun,work=work,
                    energy_outputs=[(sun,self.acct('chem',p),work*.90)])
                self.last_txn=txn
                self.counters['tree_growth']+=1
        self.counters['tree_climate_tick']+=1

    def _feed(self,r):
        p=r.habitat
        maxfuel=.34
        fuel=f'fuel:{r.id}'
        q=min(.075,max(0.,maxfuel-self.book.mass[fuel]),
              self.book.mass[self.acct('plant',p)])
        source=self.acct('chem',p)
        work=q*.33
        if q<=.001 or self.book.energy[source]<work:return False
        txn=self.book.transform([(self.acct('plant',p),fuel,q)],source=source,work=work,
                energy_outputs=[(source,f'metabolic:{r.id}',work*.9)])
        self.last_txn=txn
        self.counters['tree_grazing']+=1
        return True

    def _metabolism(self,r):
        fuel=f'fuel:{r.id}';met=f'metabolic:{r.id}';p=r.habitat
        q=min(.026,self.book.mass[fuel])
        work=q*.12
        if q>=.004 and self.book.energy[met]+1e-9>=work:
            txn=self.book.transform([(fuel,self.acct('detritus',p),q)],source=met,work=work,
                    energy_outputs=[(met,self.acct('heat',p),work*.9)])
            self.last_txn=txn
            self.counters['tree_metabolism']+=1
        else:
            r.health=max(0.,r.health-.085)
        if q<.018:r.health=max(0.,r.health-.045)
        else:r.health=min(1.,r.health+.012)

    def _migrate(self,r):
        """Local native-resident movement, now sensitive to accessible chemical energy.

        Plant mass alone cannot be eaten if the shared habitat chem account has
        no funded transform work. This is an experimental policy refinement,
        not an increase to energy supply. Only adjacent habitats are evaluated;
        travel still costs the resident's own metabolic energy.
        """
        p=r.habitat
        others=Counter(x.habitat for x in self.residents.values() if x.alive)
        choices=tuple(self.habitats[p].neighbors)
        # One full native feeding opportunity costs up to 0.075 * 0.33 chem.
        # Below that budget the resident can seek an adjacent viable feeding
        # site even when its present habitat contains abundant plant biomass.
        chem=self.book.energy[self.acct('chem',p)]
        chem_limited=chem < .075*.33
        # Forage-search friction: recently moved residents do not instantly
        # travel again unless health indicates a critical survival emergency.
        # A low-energy resident can STILL be unable to travel or starve.
        # 0 disables friction for exact previous-policy matched controls.
        last_age=getattr(r,'last_migration_age',-99999)
        if (self.migration_cooldown_days>0
                and self.age-last_age<self.migration_cooldown_days
                and r.health>=.40):
            self.counters['tree_migration_deferred']+=1
            return False
        if chem_limited:
            def forage_capacity(k):
                plant=self.book.mass[self.acct('plant',k)]
                energy=self.book.energy[self.acct('chem',k)]
                return min(plant,energy/.33)/(1+others[k])
            scores={k:forage_capacity(k) for k in (p,*choices)}
            dst=max(choices,key=lambda v:(scores[v],v))
            if scores[dst] <= max(.01,scores[p]*1.13):return False
            reason='chemical_energy_shortage'
        else:
            scores={k:self.book.mass[self.acct('plant',k)]/(1+others[k]) +
                     .08*self.book.mass[self.acct('water',k)] for k in (p,*choices)}
            dst=max(choices,key=lambda v:(scores[v],v))
            if scores[dst] <= scores[p]*1.13:return False
            reason='forage_pressure'
        met=f'metabolic:{r.id}'
        if self.book.energy[met]<.008:return False
        txn=self.book.move(energy=[(met,self.acct('heat',p),.008)])
        return_trip=(getattr(r,'last_migration_origin',None)==dst
                     and self.age-last_age<=12)
        r.habitat=dst;self.last_txn=txn
        r.last_migration_age=self.age
        r.last_migration_origin=p
        if return_trip:self.counters['tree_migration_return_12d']+=1
        self._event('tree_migration',actor=r.id,txn=txn,habitat=dst,
                    from_habitat=p,reason=reason,return_trip_12d=return_trip)
        return True

    def _death(self,r,cause):
        if not r.alive:return False
        r.alive=False
        p=r.habitat
        mats=[];ener=[]
        body=self.book.mass[f'body:{r.id}']
        fuel=self.book.mass[f'fuel:{r.id}']
        if body>0:mats.append((f'body:{r.id}',self.acct('detritus',p),body))
        if fuel>0:mats.append((f'fuel:{r.id}',self.acct('detritus',p),fuel))
        met=self.book.energy[f'metabolic:{r.id}']
        if met>0:ener.append((f'metabolic:{r.id}',self.acct('heat',p),met))
        if mats:
            # A real decay transition. Work comes from funded sunlight or House.
            work=.003
            src=self.acct('sun',p) if self.book.energy[self.acct('sun',p)]>=work else 'house'
            self.book.transform(mats,source=src,work=work,
                                energy_outputs=[(src,self.acct('heat',p),.9*work)]+ener)
        elif ener:self.book.move(energy=ener)
        self.sim.seeds.constructs.items[self.id].inhabitants.discard(r.id)
        self._event('tree_death',actor=r.id,habitat=p,cause=cause,age=r.age,
                    generation=r.generation)
        return True

    def _animals(self):
        present=[r for r in self.residents.values() if r.alive]
        rng=Random(stable_seed(self.sim.seed,self.id,self.age,'life'))
        rng.shuffle(present)
        n_alive=len(present)
        growth=0
        births=[]
        for r in present:
            r.age+=1
            if getattr(self,'disease_risk',0)>0 and rng.random()<self.disease_risk:
                r.health=max(0.,r.health-.25)
                self._event('tree_disease',actor=r.id,habitat=r.habitat)
            if r.age>r.max_age or r.health<=0:
                self._death(r,'old_age' if r.age>r.max_age else 'starvation');continue
            p=r.habitat
            low_plant=self.book.mass[self.acct('plant',p)]/(1+sum(x.alive and x.habitat==p for x in present))<.25
            low_chemical_energy=self.book.energy[self.acct('chem',p)] < .075*.33
            if low_plant or low_chemical_energy:
                self._migrate(r);p=r.habitat
            self._feed(r)
            self._metabolism(r)
            if r.health<=0:self._death(r,'starvation');continue
            # Birth is not guaranteed; it competes for food/energy and land.
            pop=sum(x.alive for x in self.residents.values())
            cap=min(65,max(8,int(sum(self.book.mass[self.acct('plant',k)] for k in self.habitats)*1.75)))
            local_plant=self.book.mass[self.acct('plant',p)]
            readiness=(r.age>=14 and self.age-r.last_birth>=9 and
                      self.book.mass[f'fuel:{r.id}']>=.17 and
                      self.book.energy[f'metabolic:{r.id}']>=.028 and
                      r.health>=.65 and local_plant>=.40 and pop<cap)
            if readiness and rng.random()<.075*max(.04,1-pop/cap):
                births.append(r)
        for parent in births:
            if parent.alive and self.book.mass[f'fuel:{parent.id}']>=.145 and self.book.energy[f'metabolic:{parent.id}']>=.023:
                self._new_resident(parent.habitat,parent=parent)
        self.counters['tree_population_tick']+=1

    def step(self):
        # Archived Trees no longer run living ecology, but their already-funded
        # physical food and fruit remain subject to maturity and decay. Advance
        # measured age only; never grant fuel or produce new resources.
        if self.state=='archived':
            # Age is measured elapsed world time, not a provisioning reward.
            # Even a Tree without the optional policy must continue aging;
            # installing the policy later must not rewind its remnant clock.
            self.age+=1
            if self.provisioning is not None:
                self.provisioning.tick()
            return
        if self.state not in ('active','germinating'):return
        if self.sim.seeds.plants[self.id]['status']!='stable' or self.sim.seeds.constructs.items[self.id].status!='stable':return
        if self.sim.seeds.constructs.items[self.realm_id].status!='stable':return
        parent=self.sim.seeds.plants[self.realm_id]
        if parent['status']!='stable':return
        self.age+=1
        start_seq=self.book.seq
        self._climate_and_plants()
        if self.state=='active':self._animals()
        if self.provisioning is not None:self.provisioning.tick()
        self.sim.seeds.plants[self.id]['inhabitants']=self.population
        snap=self._snapshot()
        eid=self._event('tree_daily_update',world_age=self.age,
             population=self.population,births=snap['births'],deaths=snap['deaths'],
             plant_biomass=snap['plants'],material_transaction_from=start_seq+1,
             material_transaction_to=self.book.seq)
        self.daily_events.append(eid)
        if len(self.daily_events)>500:self.daily_events.pop(0)

    @property
    def population(self):
        return sum(r.alive for r in self.residents.values())

    def _snapshot(self):
        data={'age':self.age,'population':self.population,
              'births':self.counters['tree_birth'],'deaths':self.counters['tree_death'],
              'plants':round(sum(self.book.mass[self.acct('plant',p)] for p in self.habitats),4),
              'soil':round(sum(self.book.mass[self.acct('soil',p)] for p in self.habitats),4),
              'water':round(sum(self.book.mass[self.acct('water',p)] for p in self.habitats)+
                           self.book.mass[f'water:tree:{self.id}:cloud'],4),
              'chemical_energy':round(sum(self.book.energy[self.acct('chem',p)] for p in self.habitats),4)}
        self.timeline.append(data)
        if len(self.timeline)>500:self.timeline.pop(0)
        return data

    def observe(self,founder):
        f=self.sim.founders.people[founder]
        if f.location not in ('house','riverbank'):
            raise ValueError('World Tree observations require House observatory or riverbank')
        q=.025
        if self.book.energy[f'founder:{founder}']<q:raise ValueError('Founder observation energy insufficient')
        txn=self.book.move(energy=[(f'founder:{founder}','environment:heat',q)])
        s=dict(self.timeline[-1]);s['age']=self.age;s['seen_tick']=self.sim.tick
        self.observations[founder]=s
        f.memories.append(f'World Tree {self.id}, tick {self.age}: pop {s["population"]}, biomass {s["plants"]:.2f}')
        # Deliver experience through the existing RSW-K cognition store. Exposure
        # is not automatically skill or complete understanding.
        knowledge_event=encounter(self.sim.knowledge,self.sim.states[founder].cognition,
                 self.sim.tick,founder,self.claim_id,source=f'world_sensor:{self.id}',
                 medium='observation',fidelity=.75,trust=.50)
        self._event('tree_observed',actor=founder,txn=txn,knowledge_event=knowledge_event,inhabitants=s['population'],
                    measured_biomass=s['plants'],world_age=self.age,
                    decision_parent=getattr(self.sim,'_current_parent',None))
        return s

    def study(self,founder):
        evidence=self.observations.get(founder)
        if evidence is None or self.sim.tick-evidence['seen_tick']>7:
            raise ValueError('research requires a recently observed World Tree')
        if self.sim.tick-self.research.get(founder,-100)<5:
            raise ValueError('research requires independent study interval')
        q=.09
        if self.book.energy[f'founder:{founder}']<q:raise ValueError('Founder research energy insufficient')
        txn=self.book.move(energy=[(f'founder:{founder}','environment:heat',q)])
        f=self.sim.founders.people[founder]
        before=f.skills.get('research',0.)
        self.sim.founders.learn(founder,'research',.008*max(.15,1-before),
              f'World Tree analysis {self.id}:{self.age}:{evidence["plants"]:.2f}')
        self.research[founder]=self.sim.tick
        self._event('tree_researched',actor=founder,txn=txn,
                   observation_age=evidence['age'],skill_gain=round(f.skills['research']-before,6),
                   decision_parent=getattr(self.sim,'_current_parent',None))
        return {'world':self.id,'observation':evidence,'skill_gain':round(f.skills['research']-before,6)}

    def enable_provisioning(self,**parameters):
        """Enable the audited U026-C003 resource policy on this real Tree."""
        from founders_civ.core.autonomous_provisioning import TreeProvisioningPolicy
        if self.provisioning is not None:raise ValueError('provisioning already enabled')
        self.provisioning=TreeProvisioningPolicy(self,**parameters)
        return self.provisioning

    @property
    def resources(self):
        """Book-backed fruit/food operations on this actual living Tree."""
        from founders_civ.core.living_assets import TreeResourceOps
        return TreeResourceOps(self)

    def make_portable_food(self,habitat,lot,**quantities):
        return self.resources.make_food(habitat,lot,**quantities)

    def grow_creation_fruit(self,habitat,lot,**quantities):
        return self.resources.grow_fruit(habitat,lot,**quantities)

    def collapse(self,cause):
        if self.state=='archived':return
        for r in list(self.residents.values()):
            if r.alive:self._death(r,'world_collapse')
        # Once the World Tree collapses, do not strand its matter inside an
        # inaccessible active-habitat account. Preserve it in traceable remnants.
        for p in self.habitats:
            q=[]
            for typ in ('soil','plant','detritus'):
                amount=self.book.mass[self.acct(typ,p)]
                if amount>0:q.append((self.acct(typ,p),f'remnant:tree:{self.id}:{p}',amount))
            if q:
                source=self.acct('sun',p)
                if self.book.energy[source]<.003 and self.book.energy['house']>=.003:
                    # Cannot use House as a transform source directly: the toll
                    # returns 70% of work to House. Fund an intermediate account.
                    source=f'work:tree_collapse:{self.id}'
                    self.book.move(energy=[('house',source,.003)])
                if self.book.energy[source]>=.003:
                    self.book.transform(q,source=source,work=.003,
                        energy_outputs=[(source,self.acct('heat',p),.0027)])
            water=self.book.mass[self.acct('water',p)]
            if water>0:self.book.move(material=[(self.acct('water',p),f'water:tree:{self.id}:remnant',water)])
            en=[]
            for typ in ('sun','chem'):
                amount=self.book.energy[self.acct(typ,p)]
                if amount>0:en.append((self.acct(typ,p),self.acct('heat',p),amount))
            if en:self.book.move(energy=en)
        cloud=f'water:tree:{self.id}:cloud'
        if self.book.mass[cloud]>0:
            self.book.move(material=[(cloud,f'water:tree:{self.id}:remnant',self.book.mass[cloud])])
        self.state='archived'
        self._event('tree_world_archived',reason=cause,
                    residents_total=len(self.residents))
        self._snapshot()

    def export(self,include_residents=False):
        row={'id':self.id,'blueprint':self.seed_id,'parent':self.realm_id,
             'owner':self.owner,'state':self.state,'age':self.age,
             'species_seeds':list(self.species_seed_ids),
             'ecology_claim':self.claim_id,'recent_ecology_events':self.daily_events[-20:],
             'population':self.population,'births':self.counters['tree_birth'],
             'deaths':self.counters['tree_death'],
             'recent':self.timeline[-1],
             'history':self.timeline[-160:],
             'habitats':[]}
        for p,h in self.habitats.items():
            people=[r for r in self.residents.values() if r.alive and r.habitat==p]
            row['habitats'].append({'id':f'{self.id}:{p}','biome':p,'neighbors':list(h.neighbors),
                 'population':len(people),'season':h.season,
                 'plant':round(self.book.mass[self.acct('plant',p)],4),
                 'soil':round(self.book.mass[self.acct('soil',p)],4),
                 'detritus':round(self.book.mass[self.acct('detritus',p)],4),
                 'water':round(self.book.mass[self.acct('water',p)],4),
                 'chem':round(self.book.energy[self.acct('chem',p)],4)})
        if include_residents:
            row['residents']=[{'id':r.id,'habitat':r.habitat,'age':r.age,
                'born_tick':r.born_tick,'generation':r.generation,
                'alive':r.alive,'parent':r.parent} for r in self.residents.values()]
        return row


class WorldTreeRegistry:
    def __init__(self,sim):
        self.sim=sim
        self.worlds:dict[str,WorldTree]={}

    def add(self,creation,blueprint):
        if creation['kind']!='world':raise ValueError('only World Tree creations have living runtimes')
        if creation['id'] in self.worlds:raise ValueError('tree already has runtime')
        new=WorldTree(self.sim,creation,blueprint)
        self.worlds[new.id]=new
        return new

    def step(self):
        for world in list(self.worlds.values()):
            world.step()

    def collapsed(self,creation_id,cause):
        t=self.worlds.get(creation_id)
        if t:t.collapse(cause)

    def export(self,include_residents=False):
        return [w.export(include_residents) for w in self.worlds.values()]
