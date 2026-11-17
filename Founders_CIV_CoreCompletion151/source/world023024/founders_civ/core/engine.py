"""Founders-CIV v0.17: FIRST INTEGRATION SMOKE ENGINE.

A small causal vertical slice, not the whole v0.13/0.14 functionality. It takes
species/energy parameters from the optimized v0.13 branch, directional source-tagged
learning from the v0.16 preflight, the v0.14 five-need/commitment vocabulary, and the
v0.16 strict transaction contract; it replaces the earlier independently mutating stocks.

Deliberate limitations: abstract one-component mass, coarse energy, no chemistry,
no births or Founder checkpoint resurrection, no higher Soul States, no actual
climate-driven water-cycle chemistry. All parameters are SYNTHETIC.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import Counter, defaultdict
from typing import Optional
import json, math, random, hashlib
from .ledger import Book

PATCH_NAMES=('forest','grassland','wetland','ridge')
WORLD_NAMES=('Solara','Vespara')
CLAIMS={'storage_helps':'supported','ritual_makes_rain':'false'}
# Provisional species physiology and potential skills adapted from v0.13.
SPECIES={
 'creation':dict(diet='omnivore',burn=.042,fuel=.024,reserve=3.0,capacity=5.,mass=2.1,mature=1000,skill='build'),
 'castor':dict(diet='omnivore',burn=.040,fuel=.022,reserve=3.8,capacity=6.,mass=2.1,mature=1000,skill='teach'),
 'meadow_grazer':dict(diet='herbivore',burn=.024,fuel=.015,reserve=2.1,capacity=6.,mass=1.65,mature=55,skill='graze'),
 'forest_browser':dict(diet='herbivore',burn=.024,fuel=.015,reserve=2.2,capacity=6.,mass=1.8,mature=70,skill='browse'),
 'ridge_hound':dict(diet='predator',burn=.045,fuel=.015,reserve=2.8,capacity=16.,mass=2.7,mature=90,skill='coordinate'),
 'shadow_stalker':dict(diet='predator',burn=.048,fuel=.015,reserve=2.8,capacity=16.,mass=2.7,mature=100,skill='sneak'),
 'carrion_bird':dict(diet='scavenger',burn=.028,fuel=.012,reserve=2.,capacity=10.,mass=1.4,mature=65,skill='scavenge'),
 'ground_scavenger':dict(diet='scavenger',burn=.028,fuel=.012,reserve=2.,capacity=10.,mass=1.4,mature=70,skill='scavenge'),
 'soil_fungus':dict(diet='decomposer',burn=.008,fuel=.006,reserve=1.,capacity=4.,mass=.4,mature=45,skill='decompose'),
 'founder':dict(diet='founder',burn=0.,fuel=0.,reserve=0.,capacity=0.,mass=0.,mature=0,skill='govern')}

@dataclass
class Agent:
    id:str
    species:str
    world:str
    patch:str
    group:str
    age:int
    needs:dict=field(default_factory=dict)
    traits:dict=field(default_factory=dict)
    beliefs:dict=field(default_factory=dict)
    skills:dict=field(default_factory=dict)
    memory:list=field(default_factory=list)
    source_memory:list=field(default_factory=list)
    practiced:dict=field(default_factory=lambda:defaultdict(int))
    expectations:dict=field(default_factory=dict)
    nodes:set=field(default_factory=set)
    conviction:float=.0
    fear:float=.2
    goal:str='survive'
    willing:float=.5
    health:float=100.
    thirst:float=16.
    alive:bool=True
    route:dict=field(default_factory=dict)
    parents:tuple=()

@dataclass
class Edge:
    source:str
    target:str
    relation:str
    trust:float
    respect:float

@dataclass
class Institution:
    id:str
    settlement:str
    proposer:str
    members:set=field(default_factory=set)
    rules:dict=field(default_factory=lambda:{'reserve_min':.06,'share_if_hungry':True})
    pooled_account:str=''
    founded:Optional[int]=None
    work_events:int=0
    monitoring_events:int=0
    revised:int=0
    public_claim:str=''
    shared_norm:bool=False

class Simulation:
    def __init__(self,seed=42,days=30,arm='1111',trace=True):
        if len(arm)!=4 or any(c not in '01' for c in arm):raise ValueError('arm must be S/F/B/I binary')
        self.seed=seed;self.days=days;self.arm=arm;self.S,self.F,self.B,self.I=(c=='1' for c in arm)
        self.trace=trace
        self.book=Book();self.actors={};self.edges=defaultdict(list)
        self.groups={};self.institutions={};self.pending={}
        self.day=0;self.events=[];self.counter=Counter();self.daily=[]
        self.event_num=0;self.witnesses=defaultdict(list)
        self.active_decision={}
        self.weather={};self.daylight={'Solara':.70,'Vespara':.40}
        self.founders={'Solara':'Solara:F0','Vespara':'Vespara:F0'}
        self.rng=random.Random(seed*173+19)
        self._setup()

    @staticmethod
    def stable_seed(*parts):
        digest=hashlib.blake2b('|'.join(map(str,parts)).encode('utf-8'),digest_size=8).digest()
        return int.from_bytes(digest,'big')

    def _actor_rng(self,a,channel):
        return random.Random(self.stable_seed(self.seed,self.day,a.id,channel))

    def _record(self,action,actor=None,transaction=None,**extra):
        self.event_num+=1
        parent=()
        if isinstance(actor,Agent) and action!='decision':
            current=self.active_decision.get(actor.id)
            if current and current[0]==self.day:parent=(current[1],)
        row=dict(event_id=self.event_num,day=self.day,action=action,
                 parent_event_ids=parent,
                 actor=actor.id if isinstance(actor,Agent) else (actor or ''),
                 world=actor.world if isinstance(actor,Agent) else extra.pop('world',''),
                 patch=actor.patch if isinstance(actor,Agent) else extra.pop('patch',''),
                 transaction_id=transaction.seq if transaction else None,
                 material=transaction.material if transaction else (),
                 energy=transaction.energy if transaction else (),
                 toll=transaction.toll if transaction else 0.,**extra)
        if self.trace:self.events.append(row)
        self.counter[action]+=1
        return self.event_num

    def _setup(self):
        b=self.book;b.seed_energy('house',300000.)
        b.seed_energy('world_toll',0.)
        for l in range(10):b.seed_energy(f'underworld:{l}',0.)
        for world in WORLD_NAMES:
            b.seed_energy(f'heat:{world}',2000.)
            b.seed_mass(f'cloud:{world}',120.)
            for patch in PATCH_NAMES:
                place=f'{world}:{patch}'
                b.seed_mass(f'soil:{place}',340.)
                b.seed_mass(f'plant:{place}',130.)
                b.seed_mass(f'detritus:{place}',35.)
                b.seed_mass(f'carcass:{place}',3.)
                b.seed_mass(f'water:{place}',130.)
                b.seed_energy(f'sun:{place}',0.)
                b.seed_energy(f'chem:{place}',260.)
                b.seed_energy(f'carrionchem:{place}',3.)
                b.seed_energy(f'detchem:{place}',20.)
            for gi in range(2):
                settlement=f'{world}:S{gi+1}'
                place=f'{world}:{"forest" if gi==0 else "grassland"}'
                b.seed_mass(f'food:{settlement}',5.0)
                b.seed_energy(f'foodchem:{settlement}',10.)
                b.seed_mass(f'water:{settlement}',8.)
                self.groups[settlement]=[]
                for i in range(24):
                    aid=f'{settlement}:C{i:02d}'
                    self._seed_actor(aid,'creation',world,place,settlement,i,age=1100+i*27)
                    self.groups[settlement].append(aid)
                cid=f'{settlement}:CASTOR'
                self._seed_actor(cid,'castor',world,place,settlement,25,age=3000)
                self.groups[settlement].append(cid)
            # Canonical fixed initial species populations, individual entities.
            for species,count,patch in [
                ('meadow_grazer',30,'grassland'),('forest_browser',30,'forest'),
                ('ridge_hound',6,'grassland'),('shadow_stalker',4,'forest'),
                ('carrion_bird',8,'ridge'),('ground_scavenger',6,'wetland'),
                ('soil_fungus',8,'forest')]:
                for i in range(count):
                    # Distribute grazers/browsers beyond their preferred habitat for migration tests.
                    chosen=patch if i%7 else ('wetland' if species=='meadow_grazer' else 'ridge')
                    aid=f'{world}:{species}:{i:03d}'
                    self._seed_actor(aid,species,world,f'{world}:{chosen}',f'{world}:wild',i,age=100+i*3)
            fid=self.founders[world]
            self._seed_actor(fid,'founder',world,f'{world}:grassland',f'{world}:House',0,age=100000)
        self._build_social()
        self.book.freeze()
        # Weather exogenous stream is not affected by F/S/B/I treatment choices.
        for world in WORLD_NAMES:
            rg=random.Random(self.stable_seed(self.seed,world,'weather'))
            self.weather[world]=[max(.05,min(1.,rg.gauss(.73,.08))) if not 12<=day<=21
                                 else max(.05,min(1.,rg.gauss(.25,.05)))
                                 for day in range(1,self.days+1)]
        # Seed two competing explanations in persons, not in the environment.
        for world in WORLD_NAMES:
            for idx,gi in enumerate((1,2)):
                castor=self.actors[f'{world}:S{gi}:CASTOR']
                castor.beliefs['storage_helps']=.96
                rumor=self.actors[f'{world}:S{gi}:C{(idx*7+3):02d}']
                rumor.beliefs['ritual_makes_rain']=.86

    def _seed_actor(self,aid,species,world,place,group,i,age):
        rg=random.Random(self.stable_seed(self.seed,aid,'traits'))
        sp=SPECIES[species]
        a=Agent(id=aid,species=species,world=world,patch=place,group=group,age=age,
                needs={'phys':rg.uniform(25,50),'safety':rg.uniform(25,53),
                       'belonging':rg.uniform(27,53),'esteem':rg.uniform(22,48),
                       'purpose':rg.uniform(29,53)},
                traits={'curiosity':rg.uniform(.2,.94),'empathy':rg.uniform(.2,.9),
                        'caution':rg.uniform(.22,.92),'ambition':rg.uniform(.22,.94)},
                skills={'forage':rg.uniform(.1,.4),'build':rg.uniform(.1,.42),
                        'teach':rg.uniform(.1,.4),'navigate':rg.uniform(.08,.39),
                        'hunt':rg.uniform(.10,.39),'coordinate':rg.uniform(.09,.4),
                        'sneak':rg.uniform(.09,.4),'grapple':rg.uniform(.09,.4),
                        'graze':rg.uniform(.10,.4),'decompose':rg.uniform(.10,.38)},
                fear=rg.uniform(.1,.35),willing=rg.uniform(.34,.87),
                goal=rg.choice(('protect_kin','master_skill','secure_food','explore')))
        if species=='castor':a.skills['teach']=.83;a.skills['build']=.65
        if species=='ridge_hound':a.skills['coordinate']+=.2
        if species=='shadow_stalker':a.skills['sneak']+=.18;a.skills['grapple']+=.12
        self.actors[aid]=a
        b=self.book
        b.seed_mass(f'body:{aid}',sp['mass'])
        b.seed_mass(f'fuel:{aid}',0.55 if species!='founder' else 0.)
        b.seed_mass(f'food:{aid}',0.38 if species in ('creation','castor') else 0.)
        b.seed_mass(f'water:{aid}',.45 if species in ('creation','castor') else 0.)
        b.seed_energy(f'reserve:{aid}',sp['reserve'])
        b.seed_energy(f'embodied:{aid}',sp['mass']*1.6)
        b.seed_energy(f'foodchem:{aid}',.76 if species in ('creation','castor') else 0.)
        # Extra initial matter/energy is a declared initial endowment, not created mid-run.
        return a

    def _build_social(self):
        for settlement,ids in sorted(self.groups.items()):
            mortal=[x for x in ids if self.actors[x].species=='creation']
            castor=[x for x in ids if self.actors[x].species=='castor'][0]
            # Actors are related to five household members, with directed asymmetry.
            for i,aid in enumerate(mortal):
                for j in range((i//6)*6,(i//6)*6+6):
                    if i!=j:self._link(mortal[j],aid,'family',.72)
                if self.S:
                    self._link(mortal[(i+6)%24],aid,'neighbor',.40)
                    self._link(mortal[(i+1)%24],aid,'friend',.57)
                    self._link(castor,aid,'mentor',.83)
            if self.S:
                for aid in mortal:self._link(aid,castor,'apprentice',.44)

    def _link(self,source,target,kind,trust):
        # Linked access is independent of unconditional truth or skill transfer.
        self.edges[target].append(Edge(source,target,kind,trust,trust+.05))

    def _phys(self,action,actor=None,material=(),energy=(),work=None,work_source=None,**extra):
        if work is not None:
            txn=self.book.transform(material,work_source,work,energy)
        else:txn=self.book.move(material,energy)
        return self._record(action,actor,txn,**extra)

    def _experience(self,a,skill,event_id,success=True,practice=False):
        if not a.alive:return
        # A memory is source-tagged, but merely hearing a claim never trains a skill.
        a.memory.append(event_id)
        if len(a.memory)>70:a.memory.pop(0)
        if practice and success:
            a.practiced[skill]+=1
            a.skills[skill]=min(1.0,a.skills.get(skill,.05)+.018)
            if a.practiced[skill]>=4 and a.skills[skill]>=.25:
                a.nodes.add(f'{skill}_node')
        expectation_action={'forage':'forage','survival':'eat','graze':'graze',
          'build':'practice','cooperate':'pledge','social':'socialize',
          'investigate':'investigate','coordinate':'institution_work',
          'comprehend':'socialize'}.get(skill,skill)
        prev=a.expectations.get(expectation_action,.5)
        a.expectations[expectation_action]=.90*prev+.10*(1. if success else 0.)
        self.counter['memory_events']+=1

    def _daily_sun(self):
        b=self.book
        txn=b.wellspring(160.)
        self._record('wellspring',transaction=txn)
        # Underworld energy cascades through ten distinct layers, eventually returning to House.
        for i in reversed(range(10)):
            src=f'underworld:{i}'
            amount=b.energy[src]*.07
            if amount>1e-10:
                dst='house' if i==9 else f'underworld:{i+1}'
                txn=b.move(energy=[(src,dst,amount)])
                self._record('underworld_flow',transaction=txn,layer=i)
        sunlight=min(b.energy['house'],60.+.30*160.)
        # Transfer all emitted energy out of House. Unabsorbed light becomes heat.
        for world in WORLD_NAMES:
            exposed=self.daylight[world]
            rain=self.weather[world][self.day-1]
            for patch in PATCH_NAMES:
                place=f'{world}:{patch}';share=sunlight/8
                capture=share*exposed*rain
                legs=[('house',f'sun:{place}',capture),('house',f'heat:{world}',share-capture)]
                self._phys('sunlight',world=world,patch=place,energy=legs,
                           daylight=exposed,weather=rain)
                # Photosynthesis (soil nutrient material -> living plant); toll only on transformation.
                soil=b.mass[f'soil:{place}'];sun=b.energy[f'sun:{place}']
                growth=min(soil*.015,sun/3.,1.1)
                if growth>.001:
                    # Bound transformation work by the actually held sunlight.
                    # (sun / 3) * 3 may round one ULP above sun when fully used.
                    work=min(sun,growth*3.)
                    self._phys('photosynthesis',world=world,patch=place,
                        material=[(f'soil:{place}',f'plant:{place}',growth)],
                        energy=[(f'sun:{place}',f'chem:{place}',work*.74),
                                (f'sun:{place}',f'heat:{world}',work*.16)],
                        work=work,work_source=f'sun:{place}')
                # Light remaining this day goes into environmental heat; no toll (no material state change).
                left=b.energy[f'sun:{place}']
                if left>1e-8:
                    self._phys('unabsorbed_light',world=world,patch=place,
                               energy=[(f'sun:{place}',f'heat:{world}',left)])
        self.counter['sunlight_emitted_EU']+=sunlight

    def _maintain(self,a):
        sp=SPECIES[a.species]
        if sp['diet']=='founder' or not a.alive:return
        b=self.book;fuel_key=f'fuel:{a.id}';reserve=f'reserve:{a.id}'
        if b.mass[fuel_key]>=sp['fuel'] and b.energy[reserve]>=sp['burn']:
            cost=sp['burn'];place=a.patch
            # Metabolic processing is one material transformation, taxed once.
            self._phys('metabolism',a,
                material=[(fuel_key,f'detritus:{place}',sp['fuel'])],
                energy=[(reserve,f'heat:{a.world}',cost*.70),
                        (reserve,f'detchem:{place}',cost*.20)],
                work=cost,work_source=reserve)
            a.needs['phys']=max(0,a.needs['phys']-.6)
        else:
            a.needs['phys']=min(100,a.needs['phys']+4.1)
            a.health=max(0,a.health-.24)
            if a.health<=0:self._die(a,'starvation')
        if a.species in ('creation','castor'):
            water=f'water:{a.id}'
            if b.mass[water]>=.028:
                self._phys('water_cycle',a,material=[(water,f'water:{a.patch}',.028)])
                a.thirst=max(0.,a.thirst-.3)
            else:
                a.thirst=min(100.,a.thirst+4.5)
            a.needs['belonging']=min(100,a.needs['belonging']+0.2)
            a.needs['purpose']=min(100,a.needs['purpose']+.22)
        a.age+=1

    def _die(self,a,cause):
        if not a.alive:return
        b=self.book
        # Body's pre-accounted embodied energy funds the death state transition.
        # This works even if a starving actor's usable metabolic reserve is empty.
        source=f'embodied:{a.id}'
        cost=b.energy[source]
        if cost<=0:
            raise AssertionError('unfunded death state: no embodied energy')
        mat=[]
        for s in ('body','fuel','food'):
            key=f'{s}:{a.id}';m=b.mass[key]
            if m>0:mat.append((key,f'carcass:{a.patch}',m))
        # Food-stored energy moves into carrion's chemical reservoir, not duplicated.
        energy=[]
        chem=b.energy[f'foodchem:{a.id}']
        if chem>0:energy.append((f'foodchem:{a.id}',f'carrionchem:{a.patch}',chem))
        reserve=b.energy[f'reserve:{a.id}']
        if reserve>0:energy.append((f'reserve:{a.id}',f'carrionchem:{a.patch}',reserve))
        energy.extend([(source,f'carrionchem:{a.patch}',cost*.60),
                       (source,f'heat:{a.world}',cost*.30)])
        eid=self._phys('death',a,material=mat,energy=energy,work=cost,work_source=source,cause=cause)
        a.alive=False
        self._experience(a,'survive',eid,False)

    def _eat_plant(self,a,amount=.065):
        b=self.book;place=a.patch;sp=SPECIES[a.species]
        source=f'plant:{place}';chem=f'chem:{place}'
        total=b.mass[source]
        if total<.025 or b.energy[chem]<.025:return False
        q=min(amount,total*.22)
        avail=min(b.energy[chem]*(q/total),.28)
        capacity=max(0,sp['capacity']-b.energy[f'reserve:{a.id}'])
        if capacity<.015:q*=.3;avail*=.3;capacity=max(0,capacity)
        if avail<.02:return False
        reward=min(avail*.67,capacity)
        energy=[(chem,f'reserve:{a.id}',reward),
                (chem,f'heat:{a.world}',avail*.90-reward)]
        try:
            eid=self._phys('graze',a,material=[(source,f'fuel:{a.id}',q)],
                energy=energy,work=avail,work_source=chem)
        except ValueError:return False
        self._experience(a,'graze',eid,True,True)
        a.needs['phys']=max(0,a.needs['phys']-2.0)
        return True

    def _harvest(self,a):
        b=self.book;place=a.patch;plant=f'plant:{place}'
        if b.mass[plant]<.05 or b.energy[f'reserve:{a.id}']<.02:return False
        q=.075*(.82+.36*a.skills['forage']);ratio=b.energy[f'chem:{place}']/max(.0001,b.mass[plant])
        en=q*ratio
        if en<=0 or en>b.energy[f'chem:{place}']:return False
        cost=.014
        try:
            eid=self._phys('harvest',a,material=[(plant,f'food:{a.id}',q)],
                energy=[(f'reserve:{a.id}',f'heat:{a.world}',cost*.9),
                        (f'chem:{place}',f'foodchem:{a.id}',en)],
                work=cost,work_source=f'reserve:{a.id}')
        except ValueError:return False
        self._experience(a,'forage',eid,True,True)
        a.needs['safety']=max(0,a.needs['safety']-.5)
        return True

    def _eat_food(self,a):
        b=self.book;stock=f'food:{a.id}'
        if b.mass[stock]<.03:return False
        q=min(.07,b.mass[stock]);chem=f'foodchem:{a.id}'
        # A full-lot fractional calculation can round one ULP above the
        # actual Book chemical balance (e.g. 0.10999999999999999 -> .11).
        # Cap work by the *existing* stock, never relax Book overdraw checks.
        avail=min(b.energy[chem],b.energy[chem]*q/max(1e-9,b.mass[stock]))
        cap=SPECIES[a.species]['capacity']-b.energy[f'reserve:{a.id}']
        if avail<.001:return False
        reward=min(avail*.65,max(0.,cap))
        eid=self._phys('eat_food',a,material=[(stock,f'fuel:{a.id}',q)],
                energy=[(chem,f'reserve:{a.id}',reward),(chem,f'heat:{a.world}',avail*.9-reward)],
                work=avail,work_source=chem)
        self._experience(a,'survival',eid,True,True)
        a.needs['phys']=max(0,a.needs['phys']-5.)
        return True

    def _fetch_water(self,a):
        b=self.book;available=b.mass[f'water:{a.patch}']
        # Weather affects accessible quantity, not the conserved total water mass.
        accessible=.095*self.weather[a.world][self.day-1]
        q=min(.09,accessible,available)
        if q<=.001:return False
        eid=self._phys('fetch_water',a,material=[(f'water:{a.patch}',f'water:{a.id}',q)],
                        accessibility=self.weather[a.world][self.day-1])
        self._experience(a,'forage',eid,True,True)
        a.thirst=max(0.,a.thirst-8.)
        return True

    def _hunt(self,a,index):
        b=self.book
        candidates=[p for p in index[a.patch] if p.alive and SPECIES[p.species]['diet']=='herbivore']
        if not candidates:
            self._migrate(a,index);return False
        if b.energy[f'reserve:{a.id}']<.12:return False
        candidates=sorted(candidates,key=lambda x:x.id)
        rg=random.Random(self.stable_seed(self.seed,self.day,a.id,'hunt'))
        prey=candidates[rg.randrange(len(candidates))]
        pack=[p for p in index[a.patch] if p.species=='ridge_hound' and p.alive]
        if a.species=='ridge_hound':
            coord=sum(p.skills['coordinate'] for p in pack)/max(1,len(pack))
            chance=min(.27,.040+.07*a.skills['hunt']+.035*min(3,len(pack)-1)*coord)
            technique='coordinate'
        else:
            chance=min(.23,.055+.085*a.skills['sneak']+.07*a.skills['grapple'])
            technique='sneak'
        cost=.055
        eid=self._phys('hunt_attempt',a,energy=[(f'reserve:{a.id}',f'heat:{a.world}',cost)],
                       target=prey.id,chance=round(chance,4),technique=technique)
        success=rg.random()<chance
        self._experience(a,technique,eid,success,True)
        self.counter['hunt_attempts']+=1
        if success:
            self.counter['hunt_successes']+=1
            self._die(prey,'predation')
            self._eat_carrion(a)
        return success

    def _eat_carrion(self,a):
        b=self.book;place=a.patch;src=f'carcass:{place}';chem=f'carrionchem:{place}'
        if b.mass[src]<.02 or b.energy[chem]<.02:return False
        q=min(.055,b.mass[src]);work=b.energy[chem]*(q/b.mass[src]);work=min(work,.25)
        if work<=.005:return False
        cap=max(0.,SPECIES[a.species]['capacity']-b.energy[f'reserve:{a.id}'])
        gain=min(work*.63,cap)
        eid=self._phys('scavenge',a,material=[(src,f'fuel:{a.id}',q)],
                energy=[(chem,f'reserve:{a.id}',gain),(chem,f'heat:{a.world}',work*.9-gain)],
                work=work,work_source=chem)
        self._experience(a,'scavenge',eid,True,True)
        return True

    def _decompose(self,a):
        b=self.book;place=a.patch;mass=f'detritus:{place}';chem=f'detchem:{place}'
        if b.mass[mass]<.015 or b.energy[chem]<.01:return False
        q=min(.04,b.mass[mass]);work=min(.11,b.energy[chem]*q/b.mass[mass])
        if work<.004:return False
        cap=max(0,SPECIES[a.species]['capacity']-b.energy[f'reserve:{a.id}'])
        reward=min(work*.38,cap)
        eid=self._phys('decompose',a,material=[(mass,f'soil:{place}',q)],
                energy=[(chem,f'reserve:{a.id}',reward),(chem,f'heat:{a.world}',work*.9-reward)],
                work=work,work_source=chem)
        self._experience(a,'decompose',eid,True,True)
        return True

    def _migrate(self,a,index):
        b=self.book
        if b.energy[f'reserve:{a.id}']<.025:return False
        destinations=[f'{a.world}:{p}' for p in PATCH_NAMES if f'{a.world}:{p}'!=a.patch]
        diet=SPECIES[a.species]['diet']
        def score(dest):
            if diet=='herbivore':val=b.mass[f'plant:{dest}']
            elif diet=='predator':val=sum(1 for x in index[dest] if x.alive and SPECIES[x.species]['diet']=='herbivore')*9.
            else:val=b.mass[f'carcass:{dest}']*3.
            return math.log1p(val)+a.route.get(dest,0.)
        dest=max(destinations,key=lambda x:(score(x),x))
        old=a.patch
        eid=self._phys('migrate',a,energy=[(f'reserve:{a.id}',f'heat:{a.world}',.025)],from_patch=old,to_patch=dest)
        a.patch=dest
        # Update patch index as actors move, not by scanning every actor.
        index[old].remove(a);index[dest].append(a)
        a.route[dest]=.85*a.route.get(dest,0.)+.15*score(dest)
        self._experience(a,'navigate',eid,True,True)
        return True

    def _animal_decision(self,a,index):
        b=self.book;sp=SPECIES[a.species];diet=sp['diet']
        fuel=b.mass[f'fuel:{a.id}'];energy=b.energy[f'reserve:{a.id}']
        if diet=='herbivore':
            if b.mass[f'plant:{a.patch}']<.8:self._migrate(a,index)
            elif fuel<.45 or energy<2.:self._eat_plant(a)
            elif self._actor_rng(a,'wander').random()<.03:self._migrate(a,index)
        elif diet=='predator':
            if fuel<.40 or energy<2.8:
                # Predators preferentially consume available carcasses rather than
                # wasting energy hunting while edible remains are present.
                if not self._eat_carrion(a):self._hunt(a,index)
            elif self._actor_rng(a,'wander').random()<.015:self._migrate(a,index)
        elif diet=='scavenger':
            if fuel<.40 or energy<2.:
                if not self._eat_carrion(a):
                    if self._actor_rng(a,'wander').random()<.1:self._migrate(a,index)
        elif diet=='decomposer':
            if fuel<.42:self._decompose(a)

    def _social_contact(self,a):
        if a.species not in ('creation','castor'):return False
        candidates=[edge for edge in self.edges[a.id] if self.actors[edge.source].alive and
                     self.actors[edge.source].patch==a.patch]
        if not candidates:return False
        rg=self._actor_rng(a,'contact')
        edge=rg.choice(candidates)
        source=self.actors[edge.source]
        if source.beliefs:
            claim=max(sorted(source.beliefs),key=lambda k:source.beliefs[k])
            if rg.random()<edge.trust*.61:
                # Claim acceptance needs communication; trust does not mean truth.
                before=a.beliefs.get(claim,0.)
                testimony=.1+.7*edge.trust*source.beliefs[claim]
                after=min(.99,max(before,testimony)+.12*before)
                a.beliefs[claim]=after
                eid=self._record('teach',source,recipient=a.id,claim=claim,
                          sender_confidence=source.beliefs[claim],receiver_confidence=after,
                          relationship=edge.relation,source_id=source.id)
                a.source_memory.append((eid,source.id,claim))
                self._experience(a,'comprehend',eid,True,False)
                a.needs['belonging']=max(0,a.needs['belonging']-.8)
                self.counter['claim_exposures']+=1
                if a.group in self.institutions and a.id in self.institutions[a.group].members:
                    self._consider_shared_norm(self.institutions[a.group],a)
                return True
        # Conversation can grow relationship without transmitting a claim.
        eid=self._record('socialize',a,partner=source.id,relation=edge.relation)
        a.needs['belonging']=max(0,a.needs['belonging']-1.1)
        self._experience(a,'social',eid,True,False)
        return True

    def _pledge(self,a):
        b=self.book
        if b.mass[f'food:{a.id}']<.045:return False
        settlement=a.group;inst=self.pending.get(settlement)
        if inst is None:
            inst=Institution(id=f'{settlement}:food_commitment',settlement=settlement,
                             proposer=a.id,pooled_account=f'food:{settlement}:pool')
            self.pending[settlement]=inst
            # Proposal alone isn't an institution; no free budget, no members created.
            self._record('proposal',a,organization=inst.id,claim='share_food')
        if a.id in inst.members:return False
        q=.045;source=f'food:{a.id}';out=inst.pooled_account
        en=b.energy[f'foodchem:{a.id}']*q/b.mass[source]
        eid=self._phys('pledge_deposit',a,material=[(source,out,q)],
                       energy=[(f'foodchem:{a.id}',f'foodchem:{settlement}:pool',en)],
                       institution=inst.id)
        inst.members.add(a.id)
        self._experience(a,'cooperate',eid,True,False)
        self._consider_shared_norm(inst,a)
        if inst.founded is None and len(inst.members)>=3 and b.mass[out]>=.13:
            inst.founded=self.day
            self.institutions[settlement]=inst
            self._record('institution_founded',a,institution=inst.id,members=sorted(inst.members),
                         pooled_food=b.mass[out],rules=dict(inst.rules))
        return True

    def _consider_shared_norm(self,inst,a):
        if not self.B or inst.shared_norm or len(inst.members)<3:return
        members=[self.actors[x] for x in sorted(inst.members)]
        claims={c:sum(m.beliefs.get(c,0.)>.55 for m in members) for c in CLAIMS}
        winner=max(sorted(claims),key=lambda k:claims[k])
        # Requires distinct adopters AND source-tracked communication; no free doctrine.
        source_events=sum(len(m.source_memory) for m in members)
        if claims[winner]>=3 and source_events>=2:
            inst.shared_norm=True;inst.public_claim=winner
            self._record('shared_norm_formed',a,institution=inst.id,claim=winner,
                         adherents=claims[winner],source_events=source_events)

    def _institution_work(self,a):
        inst=self.institutions.get(a.group)
        if inst is None or a.id not in inst.members:return False
        b=self.book
        if b.mass[inst.pooled_account]>.05:
            needy=sorted((self.actors[aid] for aid in inst.members if self.actors[aid].alive),
                         key=lambda x:(-x.needs['phys'],x.id))
            if not needy:return False
            recipient=needy[0]
            if recipient.id==a.id and a.needs['phys']<35:return False
            q=min(.035,b.mass[inst.pooled_account]-.015)
            if q<=0:return False
            src=f'foodchem:{a.group}:pool';stock=inst.pooled_account
            en=b.energy[src]*q/b.mass[stock]
            eid=self._phys('institution_distribute',a,
               material=[(stock,f'food:{recipient.id}',q)],
               energy=[(src,f'foodchem:{recipient.id}',en)],
               institution=inst.id,recipient=recipient.id,
               declared_rule=inst.rules['share_if_hungry'])
            inst.work_events+=1
            self._experience(a,'coordinate',eid,True,True)
            return True
        return False

    def _institution_monitor(self,a):
        inst=self.institutions.get(a.group)
        if not self.I or inst is None or a.id not in inst.members:return False
        inst.monitoring_events+=1
        actual=self.book.mass[inst.pooled_account]
        eid=self._record('institution_monitor',a,institution=inst.id,
                         pooled_food=actual,minimum=inst.rules['reserve_min'])
        self._experience(a,'govern',eid,True,True)
        # Rule revision requires a monitored shortage AND votes from real members.
        if actual<inst.rules['reserve_min'] and inst.monitoring_events>=3 and inst.revised==0:
            # Members must have evidence or conviction to approve; no free resources.
            voters=sum(1 for aid in inst.members if self.actors[aid].alive and
                       self.actors[aid].traits['caution']>.35)
            if voters>=math.ceil(len(inst.members)/2):
                inst.rules['reserve_min']=.025
                inst.revised+=1
                self._record('rule_revision',a,institution=inst.id,votes=voters,
                             members=len(inst.members),new_reserve=.025)
        return True

    def _individual_conviction(self,a):
        if not self.F:return
        drought=self.weather[a.world][self.day-1]<.40
        need=a.needs['phys']/100
        threat=.25 if drought else 0.
        meaning=(a.traits['caution']*need+a.traits['empathy']*a.needs['belonging']/180+threat)
        a.fear=min(1,max(0,a.fear*.94+meaning*.06))
        a.conviction=min(1,max(0,a.conviction*.994+.025*a.fear*a.willing))

    def _choose_action(self,a):
        b=self.book
        # Recompute feasible actions; no success or production modifiers from RSW.
        options=['rest','practice','socialize','investigate']
        if b.mass[f'plant:{a.patch}']>.12 and b.energy[f'reserve:{a.id}']>.02:options.append('forage')
        if b.mass[f'food:{a.id}']>.04 and b.energy[f'foodchem:{a.id}']>.05:options.append('eat')
        if b.mass[f'water:{a.patch}']>.1 and b.mass[f'water:{a.id}']<.22:options.append('fetch_water')
        if b.mass[f'food:{a.id}']>.045:options.append('pledge')
        if a.group in self.institutions:options+=['institution_work','monitor']
        if self.B and a.beliefs:options.append('ritual')
        # Prevent actor from choosing impossible institutional actions too often.
        if (not self.I or self.day%5!=0) and 'monitor' in options:options.remove('monitor')
        if a.group in self.institutions and a.id not in self.institutions[a.group].members:
            options=[x for x in options if x not in ('institution_work','monitor')]
        urgency=a.needs['phys']/100
        social=a.needs['belonging']/100
        purpose=a.needs['purpose']/100
        caution=a.traits['caution']
        scores={
          'eat':2.9*urgency+1.6*(b.mass[f'fuel:{a.id}']<.12),
          'forage':1.15+2.1*urgency+.6*caution,
          'fetch_water':1.0+1.4*(a.thirst/100)+1.5*(self.book.mass[f'water:{a.id}']<.12),
          'practice':1.10+1.2*purpose+.45*a.traits['ambition'],
          'socialize':1.05+1.4*social+.5*a.traits['empathy'],
          'investigate':1.0+.9*purpose+.55*a.traits['curiosity'],
          'rest':.5+.45*urgency,
          'pledge':.78+1.1*caution+.55*social,
          'institution_work':.8+1.15*urgency+.8*a.traits['empathy'],
          'monitor':1.75+.78*caution,
          'ritual':1.25+.50*social+.35*purpose,
        }
        if self.F:
            # F changes intent and persistence, never physical throughput per action.
            scores['pledge']+=1.35*a.conviction
            scores['forage']+=.32*a.conviction
            scores['practice']+=.23*a.conviction
        if self.B:
            if a.beliefs.get('storage_helps',0)>.6:scores['pledge']+=.9
            if a.beliefs.get('ritual_makes_rain',0)>.6:
                scores['ritual']+=1.05  # Misplaced commitment may divert effort.
        if a.group in self.institutions:
            inst=self.institutions[a.group]
            if a.id in inst.members:scores['institution_work']+=.55
        rg=self._actor_rng(a,'choose')
        for action in sorted(scores):
            scores[action]+=.20*rg.random() + .25*(a.expectations.get(action,.5)-.5)
        return max(options,key=lambda x:(scores[x],x))

    def _creation_turn(self,a):
        self._individual_conviction(a)
        action=self._choose_action(a)
        eid=self._record('decision',a,chosen_action=action,
           fear=round(a.fear,4),conviction=round(a.conviction,4),
           needs=dict(a.needs),recent_memory_ids=tuple(a.memory[-3:]),
           known_claims=dict(a.beliefs),expected_outcome=a.expectations.get(action,.5))
        self.active_decision[a.id]=(self.day,eid)
        if action=='eat':self._eat_food(a)
        elif action=='forage':self._harvest(a)
        elif action=='fetch_water':self._fetch_water(a)
        elif action=='pledge':self._pledge(a)
        elif action=='institution_work':self._institution_work(a)
        elif action=='monitor':self._institution_monitor(a)
        elif action=='socialize':self._social_contact(a)
        elif action=='practice':
            eid=self._record('practice',a,skill='build')
            self._experience(a,'build',eid,True,True)
            a.needs['esteem']=max(0.,a.needs['esteem']-.7)
        elif action=='investigate':
            # Direct evidence is kept distinct from an asserted claim.
            correct=self.weather[a.world][self.day-1]<.4
            eid=self._record('observe_weather',a,actual_drought=correct,
                              stored_weather=self.weather[a.world][self.day-1])
            self._experience(a,'investigate',eid,True,True)
            if correct and a.beliefs.get('ritual_makes_rain',0)>.1:
                # Experiencing continued drought can moderate erroneous expectations.
                a.beliefs['ritual_makes_rain']*=.85
            if correct:a.beliefs['storage_helps']=max(a.beliefs.get('storage_helps',0.),.25)
        elif action=='ritual':
            eid=self._record('ritual',a,belief=max(a.beliefs,key=a.beliefs.get))
            self._experience(a,'symbolic_practice',eid,True,False)
            a.needs['belonging']=max(0,a.needs['belonging']-.4)
        elif action=='rest':a.needs['safety']=max(0,a.needs['safety']-.4)
        # Automatic homeostatic eating is physically funded and audited.
        if self.book.mass[f'fuel:{a.id}']<.20:self._eat_food(a)
        if a.species=='castor' and self._actor_rng(a,'castor_contact').random()<.45:self._social_contact(a)

    def _snapshot(self):
        b=self.book
        living=Counter(a.species for a in self.actors.values() if a.alive)
        return dict(day=self.day,arm=self.arm,seed=self.seed,
                    creations=living['creation'],herbivores=living['meadow_grazer']+living['forest_browser'],
                    predators=living['ridge_hound']+living['shadow_stalker'],
                    scavengers=living['carrion_bird']+living['ground_scavenger'],
                    decomposers=living['soil_fungus'],
                    plant_solara=round(sum(b.mass[f'plant:Solara:{p}'] for p in PATCH_NAMES),4),
                    plant_vespara=round(sum(b.mass[f'plant:Vespara:{p}'] for p in PATCH_NAMES),4),
                    house=round(b.energy['house'],5),
                    institutions=len(self.institutions),
                    claim_exposures=self.counter['claim_exposures'],
                    nodes=sum(len(a.nodes) for a in self.actors.values()),
                    mass_error=b.audit()['mass_error'],energy_error=b.audit()['energy_error'])

    def step(self):
        self.day+=1
        self._daily_sun()
        # Every actor begins with metabolism; groups, claims and physical stocks remain shared.
        for aid in sorted(self.actors):self._maintain(self.actors[aid])
        index=defaultdict(list)
        for a in self.actors.values():
            if a.alive:index[a.patch].append(a)
        for aid in sorted(self.actors):
            a=self.actors[aid]
            if not a.alive:continue
            if a.species in ('creation','castor'):self._creation_turn(a)
            elif a.species!='founder':self._animal_decision(a,index)
        self.daily.append(self._snapshot())

    def run(self):
        for day in range(self.days):self.step()
        return self.summary()

    def summary(self):
        b=self.book;tot=b.audit()
        created=[a for a in self.actors.values() if a.species=='creation']
        alive=Counter(a.species for a in self.actors.values() if a.alive)
        return {'version':'0.17-first-integration','seed':self.seed,'arm':self.arm,'days':self.day,
          'initial_actors':len(self.actors),'alive_actors':sum(alive.values()),
          'creation_deaths':sum(not a.alive for a in created),
          'predators_alive':alive['ridge_hound']+alive['shadow_stalker'],
          'herbivores_alive':alive['meadow_grazer']+alive['forest_browser'],
          'institution_count':len(self.institutions),'institutions':[
             {'id':x.id,'members':len(x.members),'founded_day':x.founded,
              'work_events':x.work_events,'monitoring_events':x.monitoring_events,
              'rule_revisions':x.revised,'pool_material':b.mass[x.pooled_account],
              'shared_norm':x.shared_norm,'public_claim':x.public_claim}
             for x in self.institutions.values()],
          'nodes':sum(len(a.nodes) for a in self.actors.values()),
          'claim_exposures':self.counter['claim_exposures'],
          'source_memories':sum(len(a.source_memory) for a in self.actors.values()),
          'memory_events':self.counter['memory_events'],
          'harvest_events':self.counter['harvest'],'photosynthesis_events':self.counter['photosynthesis'],
          'hunting_attempts':self.counter['hunt_attempts'],
          'hunting_successes':self.counter['hunt_successes'],
          'pledges':self.counter['pledge_deposit'],
          'shared_norms':self.counter['shared_norm_formed'],
          'institution_monitoring':self.counter['institution_monitor'],
          'institution_rule_revisions':self.counter['rule_revision'],
          'total_food_for_creations':sum(b.mass[f'food:{a.id}'] for a in created),
          'avg_creation_phys_need':sum(a.needs['phys'] for a in created)/len(created),
          'avg_creation_health':sum(a.health for a in created)/len(created),
          'avg_creation_thirst':sum(a.thirst for a in created)/len(created),
          'water_collection_events':self.counter['fetch_water'],
          'final_sunlight_emitted':round(self.counter['sunlight_emitted_EU'],4),
          'daylight':self.daylight.copy(),'physical_audit':tot,
          'events_recorded':len(self.events)}
