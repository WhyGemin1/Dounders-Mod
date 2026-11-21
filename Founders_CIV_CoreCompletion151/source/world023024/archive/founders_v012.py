"""Founders-CIV v0.12: reproducible, experimental two-world simulation.
No claim of real-world ecological calibration. No free material/energy transfers.
Python 3.10+; no external dependencies. Usage: python founders_v012.py
"""
from __future__ import annotations
import csv, json, math, random, collections, statistics, sys
from dataclasses import dataclass, field
from pathlib import Path

SEED=12011
DAYS=240
OUT=Path('/mnt/data')
ELEMENTS={'C':0.70,'W':0.20,'N':0.10}  # toy bookkeeping, not stoichiometry
TOLL=.10
TOLL_SPLIT={'world':.20,'underworld':.10,'house':.70}
PATCHES=['forest','grassland','wetland','ridge']
ADJ={'forest':['grassland','ridge'], 'grassland':['forest','wetland'], 'wetland':['grassland','ridge'], 'ridge':['wetland','forest']}
SPECIES={
 'creation':{'max_age':2600,'maturity':220,'base_burn':.30,'capacity':32,'adult_mass':6.0,'fertility':.003,'gestation':90},
 'herbivore':{'max_age':720,'maturity':55,'base_burn':.18,'capacity':12,'adult_mass':1.65,'fertility':.033,'gestation':19},
 'predator':{'max_age':740,'maturity':92,'base_burn':.085,'capacity':16,'adult_mass':2.7,'fertility':.007,'gestation':41},
 'scavenger':{'max_age':680,'maturity':65,'base_burn':.13,'capacity':11,'adult_mass':1.4,'fertility':.014,'gestation':29},
 'castor':{'max_age':2000,'maturity':190,'base_burn':.30,'capacity':34,'adult_mass':6,'fertility':0,'gestation':100},
}
ACTIONS=['eat','gather','farm','cook','build','rest','socialize','share','guard','research','teach','explore','migrate','store']
IMPACT={
 'eat':(.90,.00,.02,.00,.00),'gather':(.65,.02,.02,.12,.06),'farm':(.43,.10,.08,.13,.17),
 'cook':(.56,.05,.15,.18,.12),'build':(.05,.68,.10,.28,.28),'rest':(.62,.20,.03,.00,.02),
 'socialize':(.03,.10,.88,.14,.10),'share':(.08,.10,.75,.26,.12),'guard':(.01,.85,.14,.26,.05),
 'research':(.00,.04,.03,.34,.95),'teach':(.02,.02,.65,.55,.58),
 'explore':(.02,-.17,.04,.24,.72),'migrate':(.25,.18,.00,.04,.20),'store':(.32,.69,.03,.16,.07),
}
AFFINITY={'forest':{'herbivore':.9,'predator':1.12,'scavenger':1},'grassland':{'herbivore':1.2,'predator':1.02,'scavenger':1},'wetland':{'herbivore':1.08,'predator':.9,'scavenger':1.15},'ridge':{'herbivore':.67,'predator':1.1,'scavenger':.9}}

@dataclass
class Patch:
 name:str
 env:dict
 stock:dict
 energy:float=0.
 heat:float=0.
 capacity:float=130.
 cover:float=.5
 sun_fraction:float=.25
 def move(self,src,dst,amt):
  amt=max(0.,min(amt,self.stock[src][0]));
  if amt<=0: return 0.
  f=amt/self.stock[src][0]; e=self.stock[src][1]*f
  self.stock[src][0]-=amt;self.stock[src][1]-=e
  self.stock[dst][0]+=amt;self.stock[dst][1]+=e
  return amt
 def add_detritus(self,m,e):
  self.stock['detritus'][0]+=m;self.stock['detritus'][1]+=e

@dataclass
class Agent:
 uid:int
 species:str
 patch:str
 sex:str
 age:int
 body_mass:float
 body_energy:float
 reserve:float
 water:float=0.0
 alive:bool=True
 hunger:float=25.0
 safety:float=68.0
 belong:float=50.0
 esteem:float=45.0
 purpose:float=40.0
 health:float=100.0
 reproductive_cooldown:int=0
 pregnancy:int=0
 traits:list=field(default_factory=list)
 skill:dict=field(default_factory=dict)
 belief:dict=field(default_factory=dict)
 weights:list=field(default_factory=list)
 personal_goal:int=0
 friends:set=field(default_factory=set)
 recent:collections.deque=field(default_factory=lambda:collections.deque(maxlen=40))
 route_value:dict=field(default_factory=dict)
 nodes:set=field(default_factory=set)
 schema:dict=field(default_factory=dict)
 inventory:dict=field(default_factory=lambda:{'raw_food':[0.,0.],'cooked_food':[0.,0.],'wood':[0.,0.]})
 event_count:int=0
 last_action:str=''
 def __post_init__(self):
  if not self.weights:self.weights=[1,1,1,1,1]
  if not self.skill:self.skill={a:.25 for a in ACTIONS+['hunt','graze','scavenge','evade','migration']}
  if not self.belief:self.belief={a:0. for a in ACTIONS+['hunt','graze','scavenge','evade','migration']}
  if not self.schema:self.schema=collections.defaultdict(int)

class World:
 def __init__(self,name,daylight,style,seed,uid_start):
  self.name=name;self.daylight=daylight;self.style=style;self.rng=random.Random(seed)
  self.patches={};self.agents=[];self.next_uid=uid_start;self.births=collections.Counter();self.deaths=collections.Counter()
  self.moves=collections.Counter();self.actions=collections.Counter();self.animal_actions=collections.Counter()
  self.institutions={};self.soc_events=collections.deque(maxlen=30);self.institution_events=[]
  self.toll=0.;self.sun_absorbed=0.;self.sun_incident=0.;self.sun_returned=0.;self.harvested=0.
  self.migration_learns=0;self.pred_hunts=0;self.pred_wins=0;self.founder_history=[]
  self.founder_reserve=75.;self.founder_need=[30.,35.,40.,45.,70.];self.founder_memory={}
  for p,capacity,cover,frac in [('forest',180,.83,.28),('grassland',155,.30,.35),('wetland',145,.63,.24),('ridge',85,.28,.13)]:
   # Material stock is represented by individual mass reservoirs; ALL share fixed element proportions.
   plant={'forest':120,'grassland':110,'wetland':85,'ridge':35}[p]
   det=10.;food=12.;stored=0.;goods=0.;carcass=0.
   stock={k:[0.,0.] for k in ['plant','detritus','food','stored','goods','carcass']}
   for k,m in [('plant',plant),('detritus',det),('food',food),('stored',stored),('goods',goods),('carcass',carcass)]:
    stock[k]=[float(m),float(m)*1.55 if k in ('plant','food','stored','carcass','detritus') else 0.]
   env={'C':650.,'W':430.,'N':115.}
   self.patches[p]=Patch(p,env,stock,0.,0.,capacity,cover,frac)
  for i in range(24):self.spawn('creation',PATCHES[i%4],adult=True,age=220+self.rng.randrange(350))
  for i in range(1):self.spawn('castor','forest',adult=True,age=400)
  for i in range(44):self.spawn('herbivore',PATCHES[i%4],adult=True,age=55+self.rng.randrange(120))
  for i in range(4):self.spawn('predator',PATCHES[(i+1)%4],adult=True,age=95+self.rng.randrange(130))
  for i in range(6):self.spawn('scavenger',PATCHES[i%4],adult=True,age=65+self.rng.randrange(100))
  self.initial_mass=self.mass_by_element();self.initial_energy=self.energy_total()
 def spawn(self,species,patch,adult=True,age=0,mother=None):
  self.next_uid+=1; sp=SPECIES[species]
  mass=sp['adult_mass']*(self.rng.uniform(.88,1.12) if adult else 0.32)
  energy=mass*3.0;reserve=sp['capacity']*(self.rng.uniform(.52,.85) if adult else .18)
  a=Agent(self.next_uid,species,patch,self.rng.choice(['F','M']),age,mass,energy,reserve)
  a.weights=[self.rng.uniform(.75,1.25) for _ in range(5)]
  a.personal_goal=self.rng.randrange(5);a.weights[a.personal_goal]*=1.65
  if species in ('herbivore','predator','scavenger'):
   a.weights=[1.8,1.4,.7,.5,.5];a.weights[a.personal_goal]+=self.rng.uniform(0,.2)
  a.skill={k:self.rng.uniform(.08,.48) for k in ACTIONS+['hunt','graze','scavenge','evade','migration']}
  a.belief={k:0. for k in a.skill}
  a.route_value={p:self.rng.uniform(-.2,.2) for p in PATCHES}
  if mother is not None:
   # Offspring are assembled entirely from maternal body material and energy reserves.
   mass=min(mother.body_mass*.18,mass)
   if mass<=0:return None
   energy=mass*3.0;reserve=min(mother.reserve*.22,2.2)
   mother.body_mass-=mass;mother.body_energy-=energy;mother.reserve-=reserve
   a.body_mass=mass;a.body_energy=energy;a.reserve=reserve
   a.skill={k:0.07 for k in a.skill};a.route_value={p:0. for p in PATCHES}
   a.sex=self.rng.choice(['F','M']);a.age=0
   self.births[species]+=1
  self.agents.append(a)
  return a
 def mass_by_element(self):
  d=collections.defaultdict(float)
  for p in self.patches.values():
   for k,v in p.env.items():d[k]+=v
   for m,e in p.stock.values():
    for k,r in ELEMENTS.items():d[k]+=m*r
  for a in self.agents:
   if not a.alive:continue
   for k,r in ELEMENTS.items():d[k]+=a.body_mass*r
   for m,e in a.inventory.values():
    for k,r in ELEMENTS.items():d[k]+=m*r
   d['W']+=a.water
  return dict(d)
 def energy_total(self):
  s=self.founder_reserve
  for p in self.patches.values():s+=p.energy+p.heat+sum(e for m,e in p.stock.values())
  for a in self.agents:
   if a.alive:s+=a.reserve+a.body_energy+sum(e for m,e in a.inventory.values())
  return s
 def living(self,species=None):return [a for a in self.agents if a.alive and (species is None or a.species==species)]

class Simulation:
 def __init__(self,seed=SEED,days=DAYS,logs=True):
  self.seed=seed;self.days=days;self.logs=logs;self.house=350000.;self.underworld=[0.]*10
  self.wellspring=0.;self.sun_emitted=0.;self.returned=0.;self.founder_drawn=0.;self.house_toll_since_sun=0.
  self.worlds=[World('Solara',.72,'steward',seed+11,10000),World('Vespara',.38,'adapt',seed+11,20000)]
  # Same agent profiles / starting inventory with matched RNG. Independently numbered IDs.
  self.initial_energy=self.all_energy();self.initial_mass={w.name:w.mass_by_element() for w in self.worlds}
  self.rows=[];self.events=[];self.audits=[];self.birth_events=[]
 def all_energy(self):return self.house+sum(self.underworld)+sum(w.energy_total() for w in self.worlds)
 def toll(self,w,p,amount):
  if amount<0:raise AssertionError('negative toll')
  p.energy+=amount*TOLL_SPLIT['world'];self.underworld[0]+=amount*TOLL_SPLIT['underworld'];self.house+=amount*TOLL_SPLIT['house'];w.toll+=amount;self.house_toll_since_sun+=amount*TOLL_SPLIT['house']
 def spend(self,w,a,cost,state=True):
  if cost<=0:return True
  if a.reserve+1.e-10<cost:return False
  a.reserve-=cost
  t=cost*TOLL if state else 0.;self.toll(w,w.patches[a.patch],t)
  w.patches[a.patch].heat+=cost-t
  return True
 def experience(self,w,a,action,day,success,reward=0,context=''):
  a.event_count+=1;a.last_action=action
  a.recent.append((day,action,int(success),context))
  a.belief[action]=.87*a.belief.get(action,0)+.13*(1. if success else -1.)
  if success:
   a.skill[action]=min(1.5,a.skill.get(action,.1)+.008+reward*.006)
   # Soul Nodes are learned through connected, remembered successes of a type, never elapsed time.
   group={'farm':'cultivation','gather':'cultivation','graze':'foraging','scavenge':'foraging','eat':'foraging','hunt':'tracking',
          'migrate':'navigation','migration':'navigation','explore':'navigation',
          'build':'crafting','cook':'crafting','teach':'teaching','research':'teaching',
          'share':'social','socialize':'social','guard':'defense','evade':'defense'}.get(action,'physical')
   past=sum(1 for d,k,ok,c in a.recent if ok and {'cultivation':('farm','gather'), 'foraging':('graze','scavenge','eat'),
        'tracking':('hunt',),'navigation':('migrate','migration','explore'),'crafting':('build','cook'),
        'teaching':('teach','research'),'social':('share','socialize'),'defense':('guard','evade')}.get(group,(action,)).__contains__(k))
   if past>=4 and a.skill[action]>=.3:a.schema[group]=a.schema.get(group,0)+1
   if a.schema.get(group,0)>=8:a.nodes.add(group)
  if self.logs and a.species in ('creation','castor'):
   self.events.append({'day':day,'world':w.name,'actor':a.uid,'species':a.species,'patch':a.patch,
       'action':action,'success':int(success),'reward':round(reward,3),'reserve':round(a.reserve,3),
       'hunger':round(a.hunger,2),'safety':round(a.safety,2),'belong':round(a.belong,2),
       'esteem':round(a.esteem,2),'purpose':round(a.purpose,2), 'skill':round(a.skill.get(action,0),3),'nodes':len(a.nodes),'context':context})
 def action_consume(self,w,a,stock_name,desired,day):
  p=w.patches[a.patch];src=a.inventory[stock_name[1:]] if stock_name.startswith('@') else p.stock[stock_name]
  available=src[0]
  take=min(available,desired)
  if take<=1.e-5:return False,0.
  en=take/available*src[1]
  src[0]-=take;src[1]-=en
  # Food changes into body and waste: all matter transferred; chemical energy redistributed.
  body_gain=min(take*.08,max(0,SPECIES[a.species]['adult_mass']*1.22-a.body_mass));a.body_mass+=body_gain
  body_en=3.0*body_gain;a.body_energy+=body_en
  waste=take-body_gain
  # 10% toll applied on the metabolic conversion energy.
  t=.1*en; self.toll(w,p,t)
  det_share=.08 if stock_name=='@cooked_food' else .13
  usable_share=.65 if stock_name=='@cooked_food' else .60
  p.add_detritus(waste,en*det_share)
  a.reserve+=en*usable_share;p.heat+=max(0.,en-body_en-t-en*det_share-en*usable_share)
  if a.reserve>SPECIES[a.species]['capacity']:
   extra=a.reserve-SPECIES[a.species]['capacity'];a.reserve-=extra;p.heat+=extra
  a.hunger=max(0,a.hunger-16*take)
  a.health=min(100,a.health+.08*take)
  return True,take
 def drink(self,w,a):
  p=w.patches[a.patch];q=min(.06,p.env['W'],max(0,.35-a.water));p.env['W']-=q;a.water+=q
 def maintenance(self,w,a,day):
  p=w.patches[a.patch];a.age+=1;a.reproductive_cooldown=max(0,a.reproductive_cooldown-1)
  a.hunger=min(100,a.hunger+(1.9 if a.species in ('creation','castor') else 2.3))
  if a.species in ('creation','castor'):
   a.belong=max(0,a.belong-.32);a.esteem=max(0,a.esteem-.22);a.purpose=max(0,a.purpose-.27)
   risk=sum(x.alive and x.species=='predator' and x.patch==a.patch for x in w.agents)
   shelter=min(1.,w.patches[a.patch].stock['goods'][0]/12)
   a.safety=max(0,min(100,a.safety-.34-.12*risk+.3*shelter))
  if a.water<.11:self.drink(w,a)
  # Small direct sunlight recharge from the patch's accessible solar reservoir.
  if p.energy>.035 and a.reserve<SPECIES[a.species]['capacity']:
   q=min(.035,p.energy,SPECIES[a.species]['capacity']-a.reserve);p.energy-=q;a.reserve+=q
  if a.reserve<.55 and a.body_mass>.5:
   # Emergency body-catabolism: existing biomass converted into usable energy, no free recovery.
   amount=min(.12,a.body_mass-.4); e=amount*3.0
   a.body_mass-=amount;a.body_energy-=e;p.add_detritus(amount,0.)
   self.toll(w,p,e*.1);a.reserve+=e*.7;p.heat+=e*.2
  # Water cycling; individual hydration storage is distinct from environmental water.
  used=min(a.water,.035);a.water-=used;p.env['W']+=used
  c=SPECIES[a.species]['base_burn']
  available=min(a.reserve,c);self.spend(w,a,available,state=True)
  if available<c-.0001:a.health-=1.6
  if a.hunger>83:a.health-=.9
  if a.age>SPECIES[a.species]['max_age']:
   a.health-=.12*(1+(a.age-SPECIES[a.species]['max_age'])/40)
  # Interact with living material only through its stock and energy (no spontaneous matter loss).
  if a.health<=0 or a.body_mass<.06:self.die(w,a,'age_or_starvation')
 def die(self,w,a,reason):
  if not a.alive:return
  p=w.patches[a.patch]
  # Death is a body-state transition; charge the universal toll from internal energy.
  death_work=min(.22,a.reserve*.10)
  a.reserve-=death_work;self.toll(w,p,death_work*TOLL);p.heat+=death_work*(1-TOLL)
  p.stock['carcass'][0]+=a.body_mass;p.stock['carcass'][1]+=a.body_energy+a.reserve*.65
  for k,(m,e) in a.inventory.items():
   dest='food' if k in ('raw_food','cooked_food') else 'goods'
   p.stock[dest][0]+=m;p.stock[dest][1]+=e
   a.inventory[k]=[0.,0.]
  p.heat+=a.reserve*.35
  p.env['W']+=a.water
  a.body_mass=0;a.body_energy=0;a.reserve=0;a.water=0;a.alive=False;w.deaths[a.species]+=1
 def plant_growth(self,w,p,day):
  # Irradiance energy is already in p.energy. Change of state: env elements -> organized biomass.
  budget=p.energy*.79
  cap=max(0,p.capacity-p.stock['plant'][0])*.22
  grow=min(budget/(1.55/.9),cap,p.env['C']/.7,p.env['W']/.2,p.env['N']/.1)
  grow=max(0,grow)
  if grow<=0:return
  src=grow*1.55/.9; p.energy-=src
  self.toll(w,p,src*.10)
  p.stock['plant'][0]+=grow;p.stock['plant'][1]+=grow*1.55
  for k,f in ELEMENTS.items():p.env[k]-=grow*f
 def decay(self,w,p):
  for stock,rate in [('detritus',.09),('carcass',.06),('goods',.002),('food',.018),('stored',.006)]:
   m=p.stock[stock][0];q=min(m,m*rate)
   if q<=0:continue
   if stock in ('goods','food','stored','carcass'):
    p.move(stock,'detritus',q)
   else:
    en=p.stock[stock][1]*(q/m)
    p.stock[stock][0]-=q;p.stock[stock][1]-=en
    for k,f in ELEMENTS.items():p.env[k]+=q*f
    t=en*TOLL;self.toll(w,p,t);p.heat+=en-t
 def migration(self,w,a,day):
  current=a.patch
  targets=ADJ[current]
  scores=[]
  for d in targets:
   p=w.patches[d]
   food=p.stock['plant'][0] if a.species in ('herbivore','creation','castor') else (p.stock['carcass'][0] if a.species=='scavenger' else len([x for x in w.agents if x.alive and x.species=='herbivore' and x.patch==d]))
   perceived=math.log1p(food)*.42+a.route_value.get(d,0)*.65+w.rng.gauss(0,.25)
   if a.species=='herbivore':perceived-=len([x for x in w.agents if x.alive and x.species=='predator' and x.patch==d])*.23
   scores.append((perceived,d))
  if not scores:return False
  _,new=max(scores)
  if not self.spend(w,a,.12):return False
  a.patch=new;w.moves[a.species]+=1
  p=w.patches[new];success=p.stock['plant'][0]>8 if a.species in ('herbivore','creation','castor') else (p.stock['carcass'][0]>.4 or len([x for x in w.agents if x.alive and x.species=='herbivore' and x.patch==new])>0)
  a.route_value[new]=.8*a.route_value[new]+.2*(1 if success else -.65)
  self.experience(w,a,'migrate' if a.species in ('creation','castor') else 'migration',day,success,context=new)
  return True
 def animal_step(self,w,a,day):
  p=w.patches[a.patch];rng=w.rng
  a.hunger=min(100,a.hunger+2.0)
  if a.species=='herbivore':
   if p.stock['plant'][0]>5 and a.reserve<SPECIES['herbivore']['capacity']*.90:
    self.spend(w,a,.12)
    ok,q=self.action_consume(w,a,'plant',rng.uniform(.24,.43),day)
    self.experience(w,a,'graze',day,ok,reward=min(1,q))
    w.animal_actions['graze']+=1
   elif p.stock['plant'][0]<6 or a.reserve<3:
    self.migration(w,a,day);w.animal_actions['migrate']+=1
   else:w.animal_actions['rest']+=1
   # Instinctive vigilance + trainable escape skill, no obligatory death in an encounter.
   if rng.random()<.06:a.skill['evade']=min(1.5,a.skill['evade']+.003)
  elif a.species=='predator':
   prey=[x for x in w.agents if x.alive and x.species=='herbivore' and x.patch==a.patch]
   if p.stock['carcass'][0]>.65 and a.reserve<12:
    self.action_consume(w,a,'carcass',rng.uniform(1.1,2.0),day);w.animal_actions['scavenge']+=1
   elif a.reserve<11 and prey:
    w.pred_hunts+=1;self.spend(w,a,.095)
    target=rng.choice(prey)
    chance=max(.025,min(.38,.09+.14*a.skill['hunt']-.09*target.skill['evade']+.035*(1-p.cover)+.018*(a.reserve/16)))
    ok=rng.random()<chance
    self.experience(w,a,'hunt',day,ok,context=f'prey={target.uid};p={chance:.3f}')
    if ok:
     w.pred_wins+=1;self.die(w,target,'hunted');self.action_consume(w,a,'carcass',rng.uniform(1.30,2.35),day)
    else:
     # Escaped prey create an event and improve ability.
     self.experience(w,target,'evade',day,True,context='escaped predator')
    w.animal_actions['hunt']+=1
   elif not prey and a.reserve<12:
    self.migration(w,a,day);w.animal_actions['migrate']+=1
   elif p.stock['carcass'][0]>.2 and a.reserve<10:
    self.action_consume(w,a,'carcass',.8,day);w.animal_actions['scavenge']+=1
   else:w.animal_actions['rest']+=1
  else:
   if p.stock['carcass'][0]>.22 and a.reserve<10:
    self.spend(w,a,.1);ok,q=self.action_consume(w,a,'carcass',rng.uniform(.24,.40),day)
    self.experience(w,a,'scavenge',day,ok,reward=q);w.animal_actions['scavenge']+=1
   elif p.stock['plant'][0]>.5 and a.reserve<8:
    self.action_consume(w,a,'plant',rng.uniform(.22,.38),day);w.animal_actions['omnivory']+=1
   elif a.reserve<7:self.migration(w,a,day);w.animal_actions['migrate']+=1
   else:w.animal_actions['rest']+=1
  if a.reproductive_cooldown==0 and a.sex=='F' and a.age>=SPECIES[a.species]['maturity']:
   partners=sum(1 for x in w.agents if x.alive and x.species==a.species and x.sex=='M' and x.age>=SPECIES[a.species]['maturity'] and x.patch==a.patch)
   if partners and a.reserve>SPECIES[a.species]['capacity']*.38 and a.body_mass>SPECIES[a.species]['adult_mass']*.72:
    if a.pregnancy==0 and rng.random()<SPECIES[a.species]['fertility']:a.pregnancy=SPECIES[a.species]['gestation']
  if a.pregnancy>0:
   a.pregnancy-=1
   if a.pregnancy==0 and a.alive and a.body_mass>SPECIES[a.species]['adult_mass']*.68:
    # Baby fully funded from maternal body and reserve.
    child=w.spawn(a.species,a.patch,adult=False,mother=a)
    if child:
     a.reproductive_cooldown=SPECIES[a.species]['gestation']*2
     birth_work=min(.14,a.reserve*.04)
     self.spend(w,a,birth_work)
     self.birth_events.append({'day':day,'world':w.name,'mother':a.uid,'baby':child.uid,'species':a.species})
 def choose_creation(self,w,a,day):
  p=w.patches[a.patch]
  physiological=min(1,max((SPECIES[a.species]['capacity']-a.reserve)/SPECIES[a.species]['capacity'],a.hunger/120))
  urg=[physiological,1-a.safety/100,1-a.belong/100,1-a.esteem/100,1-a.purpose/100]
  legal=['rest','socialize','guard','research','teach','explore','migrate']
  if p.stock['food'][0]>.2 or p.stock['stored'][0]>.2 or p.stock['plant'][0]>.3 or a.inventory['raw_food'][0]>.2 or a.inventory['cooked_food'][0]>.2:legal+=['eat','share','store','cook']
  if p.stock['plant'][0]>.25:legal+=['gather','farm','build']
  if p.stock['food'][0]<.3 and p.stock['plant'][0]<.3 and a.inventory['raw_food'][0]<.2 and a.inventory['cooked_food'][0]<.2:legal=[x for x in legal if x not in ['eat','share','store','cook']]
  if a.reserve<.25:legal=['eat'] if 'eat' in legal else ['migrate','rest']
  scores=[]
  for k in legal:
   impact=IMPACT[k]
   score=100*sum(u*x*weight for u,x,weight in zip(urg,impact,a.weights))
   score+=a.belief[k]*10+a.skill[k]*3+w.rng.gauss(0,5)
   if k=='eat':score+=(34 if a.reserve<9 else -38 if a.reserve>26 else 0)
   if k=='rest':score+=(12 if a.reserve<5 else -24 if a.reserve>23 else -6)
   if k in ('farm','gather'):
    score+=(-16 if p.stock['plant'][0]<3 else 21 if p.stock['food'][0]<4 else -8)
   if k=='migrate':score+= (74 if p.stock['plant'][0]<2 and p.stock['food'][0]<1 else 22 if p.stock['plant'][0]<9 else -28)
   if k=='share' and p.stock['food'][0]+a.inventory['raw_food'][0]<3:score-=20
   if k=='share' and p.stock['food'][0]>2 and any(x.alive and x.uid in a.friends and x.reserve<8 for x in w.agents):score+=18
   if k=='build' and p.stock['goods'][0]<4 and a.safety<76:score+=16
   if k=='guard' and a.safety<50:score+=14
   if k=='socialize' and a.belong<52:score+=18
   if k=='teach' and a.species=='castor':score+=18
   if k=='cook' and a.inventory['raw_food'][0]<.8:score-=35
   if k=='store' and p.stock['stored'][0]<10:score+=4
   if k=='guard' and len([x for x in w.agents if x.alive and x.species=='predator' and x.patch==a.patch])>1:score+=13
   scores.append((score,k))
  return max(scores)[1]
 def creation_action(self,w,a,day):
  p=w.patches[a.patch];rng=w.rng
  action=self.choose_creation(w,a,day);ok=False;reward=0;context=''
  if action=='eat':
   stock=('@cooked_food' if a.inventory['cooked_food'][0]>.2 else '@raw_food' if a.inventory['raw_food'][0]>.2 else 'food' if p.stock['food'][0]>.2 else 'stored' if p.stock['stored'][0]>.2 else 'plant')
   ok,portion=self.action_consume(w,a,stock,rng.uniform(.5,.9),day);reward=portion
  elif action in ('farm','gather'):
   q=min(p.stock['plant'][0],rng.uniform(.5,1.25)*(1+.35*a.skill[action]))
   if q>.05 and self.spend(w,a,.2):
    if action=='gather':
     en=q/p.stock['plant'][0]*p.stock['plant'][1]
     p.stock['plant'][0]-=q;p.stock['plant'][1]-=en
     a.inventory['raw_food'][0]+=q;a.inventory['raw_food'][1]+=en
    else:p.move('plant','food',q)
    w.harvested+=q;ok=True;reward=q
  elif action=='cook':
   if a.inventory['raw_food'][0]>=.35 and self.spend(w,a,.35):
    # Explicit, conservative raw->cooked material-state transition.
    q=min(.9,a.inventory['raw_food'][0]);en=q/a.inventory['raw_food'][0]*a.inventory['raw_food'][1]
    a.inventory['raw_food'][0]-=q;a.inventory['raw_food'][1]-=en
    a.inventory['cooked_food'][0]+=q;a.inventory['cooked_food'][1]+=en
    a.safety=min(100,a.safety+1);a.esteem=min(100,a.esteem+2);ok=True;reward=.7
  elif action=='build':
   q=min(p.stock['plant'][0],.8)
   if q>.2 and self.spend(w,a,.65):
    p.move('plant','goods',q);ok=True;reward=q;a.safety=min(100,a.safety+3.5)
  elif action=='store':
   q=min(a.inventory['raw_food'][0],.8)
   if q>.2 and self.spend(w,a,.18):
    en=q/a.inventory['raw_food'][0]*a.inventory['raw_food'][1]
    a.inventory['raw_food'][0]-=q;a.inventory['raw_food'][1]-=en
    p.stock['stored'][0]+=q;p.stock['stored'][1]+=en
    ok=True;reward=q;a.safety=min(100,a.safety+2)
  elif action=='rest':
   # Rest reduces fatigue and vulnerability; it does not create energy.
   a.health=min(100,a.health+.14);a.safety=min(100,a.safety+1.6);ok=True;reward=.2
  elif action=='socialize':
   others=[x for x in w.agents if x.alive and x.uid!=a.uid and x.species in ('creation','castor') and x.patch==a.patch]
   if others and self.spend(w,a,.12):
    b=rng.choice(others);a.friends.add(b.uid);b.friends.add(a.uid)
    a.belong=min(100,a.belong+5);b.belong=min(100,b.belong+3)
    ok=True;reward=1;context=f'with={b.uid}'
  elif action=='share':
   others=[x for x in w.agents if x.alive and x.uid!=a.uid and x.species in ('creation','castor') and x.patch==a.patch]
   if others and a.inventory['raw_food'][0]>.25 and self.spend(w,a,.15):
    b=min(others,key=lambda x:x.reserve);q=min(.5,a.inventory['raw_food'][0]);
    # Direct item transfer preserves matter and chemical energy.
    en=q/a.inventory['raw_food'][0]*a.inventory['raw_food'][1]
    a.inventory['raw_food'][0]-=q;a.inventory['raw_food'][1]-=en
    b.inventory['raw_food'][0]+=q;b.inventory['raw_food'][1]+=en
    ok=True
    if ok:a.friends.add(b.uid);b.friends.add(a.uid);a.belong=min(100,a.belong+5);a.esteem=min(100,a.esteem+3);reward=q;context=f'helped={b.uid}'
  elif action=='guard':
   if self.spend(w,a,.25):a.safety=min(100,a.safety+4);a.esteem=min(100,a.esteem+1);ok=True;reward=.6
  elif action=='research':
   if self.spend(w,a,.4):a.purpose=min(100,a.purpose+3.8);a.esteem=min(100,a.esteem+1.4);ok=True;reward=.8
  elif action=='teach':
   others=[x for x in w.agents if x.alive and x.uid!=a.uid and x.species in ('creation','castor') and x.patch==a.patch]
   if others and self.spend(w,a,.25):
    b=rng.choice(others);topic=max(a.skill,key=a.skill.get)
    b.skill[topic]=min(1.5,b.skill[topic]+.012)
    a.belong=min(100,a.belong+2);a.esteem=min(100,a.esteem+3);b.belong=min(100,b.belong+2)
    a.friends.add(b.uid);b.friends.add(a.uid);ok=True;reward=.8;context=f'taught={b.uid};skill={topic}'
  elif action=='explore':
   if self.spend(w,a,.25):
    dest=rng.choice(ADJ[a.patch]);pnext=w.patches[dest]
    a.route_value[dest]=.9*a.route_value[dest]+.1*(pnext.stock['plant'][0]/50)
    a.purpose=min(100,a.purpose+4);ok=True;reward=.6;context=dest
  elif action=='migrate':
   ok=self.migration(w,a,day);reward=.8 if ok else 0
   # migration function already calls experience
   w.actions[action]+=1;return
  w.actions[action]+=1
  self.experience(w,a,action,day,ok,reward,context)
  if ok and action in ('share','store','guard','teach','research','socialize'):
   w.soc_events.append((day,action,a.patch))
 def creation_reproduction(self,w,a,day):
  if a.species!='creation' or a.sex!='F' or a.age<SPECIES['creation']['maturity']:return
  partners=[b for b in w.agents if b.alive and b.species=='creation' and b.sex=='M' and b.patch==a.patch and (b.uid in a.friends)]
  if partners and a.reproductive_cooldown==0 and a.pregnancy==0 and a.reserve>17 and a.body_mass>5:
   if w.rng.random()<SPECIES['creation']['fertility']:a.pregnancy=SPECIES['creation']['gestation']
  if a.pregnancy>0:
   a.pregnancy-=1
   if a.pregnancy==0 and a.body_mass>4:
    child=w.spawn('creation',a.patch,adult=False,mother=a)
    if child:
     child.friends.add(a.uid);a.friends.add(child.uid)
     a.reproductive_cooldown=180
     self.birth_events.append({'day':day,'world':w.name,'mother':a.uid,'baby':child.uid,'species':'creation'})
 def institutions(self,w,day):
  # Endogenous collective patterns. No institution predetermined to form on a given day.
  recent=[(d,a,p) for d,a,p in w.soc_events if day-d<30]
  for patch in PATCHES:
   locals=[a for a in w.agents if a.alive and a.species in ('creation','castor') and a.patch==patch]
   friends=sum(len(a.friends) for a in locals)
   for institution,acts,threshold,relationship in [('granary',('share','store'),8,2),('watch',('guard',),8,1),('school',('teach','research'),10,3)]:
    key=f'{patch}:{institution}'
    count=sum(1 for d,a,p in recent if p==patch and a in acts)
    if key not in w.institutions and count>=threshold and friends>=relationship:
     w.institutions[key]=day;w.institution_events.append({'day':day,'world':w.name,'patch':patch,'type':institution,'evidence_events':count,'bonds':friends})
  # Institutions influence future outcomes through actual costs, not automatic free resources.
  for patch in PATCHES:
   if f'{patch}:granary' in w.institutions:
    p=w.patches[patch];q=min(.14,p.stock['food'][0]);p.move('food','stored',q)
 def founder(self,w,day):
  if day%30!=0:return
  r=w.rng; pop=w.living('creation')
  hunger=statistics.mean(a.hunger for a in pop) if pop else 100
  plant=sum(p.stock['plant'][0] for p in w.patches.values())
  choices=[]
  # Founder controls daylight but doesn't command creations.
  if w.style=='steward':
   if plant<240 or hunger>63:choices.append(('increase',3+max(0,240-plant)/80+hunger/30))
   if plant>570:choices.append(('decrease',4))
   choices.append(('observe',5.5))
  else:
   if plant<270 or hunger>55:choices.append(('increase',3.5+max(0,270-plant)/65+hunger/22))
   if plant>520:choices.append(('decrease',3.2))
   choices.append(('observe',4.5))
  decision=max(choices,key=lambda z:z[1]+r.gauss(0,.45))[0]
  if decision=='increase' and w.daylight<.85:w.daylight=min(.85,w.daylight+.06)
  if decision=='decrease' and w.daylight>.25:w.daylight=max(.25,w.daylight-.05)
  if decision!='observe':
   # Founder cost comes from explicit reserves and returns via state-change toll.
   cost=1.5
   if w.founder_reserve>=cost:
    w.founder_reserve-=cost;p=w.patches['forest'];self.toll(w,p,cost*TOLL);p.heat+=cost*(1-TOLL)
  w.founder_history.append({'day':day,'action':decision,'daylight':round(w.daylight,3),'hunger':round(hunger,2),'plant':round(plant,2)})
 def animal_culture(self,w):
  # Individuals may learn successful habitat locations from conspecifics.
  for p in PATCHES:
   for sp in ('herbivore','predator','scavenger'):
    group=[a for a in w.agents if a.alive and a.species==sp and a.patch==p]
    if len(group)>1:
     tutor=max(group,key=lambda x:x.route_value.get(p,0))
     learner=w.rng.choice(group)
     if learner.uid!=tutor.uid and tutor.route_value[p]>learner.route_value[p]+.2:
      learner.route_value[p]+=.12*(tutor.route_value[p]-learner.route_value[p]);w.migration_learns+=1
 def pass_underworld(self):
  # Simultaneous one-layer-per-day transfer (not instantaneous teleportation).
  prev=list(self.underworld)
  for i in range(9,0,-1):
   q=min(25.,prev[i-1]);self.underworld[i-1]-=q;self.underworld[i]+=q
  q=min(25.,prev[-1]);self.underworld[-1]-=q;self.house+=q;self.returned+=q
  return q
 def sun(self,day):
  returned_now=self.pass_underworld()
  previous_direct=self.house_toll_since_sun;self.house_toll_since_sun=0.
  well=140.;self.house+=well;self.wellspring+=well
  # Incoming House energy = Wellspring + delivered Underworld energy + immediate toll-to-House flows.
  incoming=well+returned_now+previous_direct # previously received direct toll + new Underworld arrival
  output=min(self.house,120+.55*incoming)
  self.house-=output;self.sun_emitted+=output
  per_world=output/len(self.worlds)
  season=.90+.20*math.sin(2*math.pi*(day-35)/120)
  for w in self.worlds:
   w.sun_incident+=per_world
   sun_factor=min(1,max(0,w.daylight*season))
   absorbed=per_world*sun_factor
   w.sun_absorbed+=absorbed;w.sun_returned+=per_world-absorbed
   self.house+=per_world-absorbed # reflected sunlight, transfer not new energy
   for p in w.patches.values():p.energy+=absorbed*p.sun_fraction
 def audit(self,day):
  expected=self.initial_energy+self.wellspring
  actual=self.all_energy()
  energy_err=actual-expected
  mass_err=0
  for w in self.worlds:
   measured=w.mass_by_element()
   for k in ELEMENTS:mass_err=max(mass_err,abs(measured[k]-self.initial_mass[w.name][k]))
  neg=[]
  for w in self.worlds:
   for p in w.patches.values():
    for k,v in p.env.items():
     if v< -1.e-7:neg.append((w.name,p.name,k,v))
    for k,(m,e) in p.stock.items():
     if min(m,e)< -1.e-7:neg.append((w.name,p.name,k,m,e))
    if min(p.energy,p.heat)< -1.e-7:neg.append((w.name,p.name,'energy_or_heat',p.energy,p.heat))
   for a in w.living():
    if min(a.body_mass,a.body_energy,a.reserve,a.water,*[z for pair in a.inventory.values() for z in pair])< -1.e-7:neg.append(('agent',a.uid))
  if abs(energy_err)>1.e-5 or mass_err>1.e-5 or neg:
   raise AssertionError(f'day {day} energy_err {energy_err} mass_err {mass_err} negatives {neg[:3]}')
  self.audits.append({'day':day,'energy_error':energy_err,'max_element_error':mass_err})
 def day_step(self,day):
  self.sun(day)
  for w in self.worlds:
   for p in w.patches.values():
    self.plant_growth(w,p,day);self.decay(w,p)
    # Daylight not immediately captured by biomass degrades into low-grade heat.
    dissipated=p.energy*.48;p.energy-=dissipated
    self.toll(w,p,dissipated*TOLL);p.heat+=dissipated*(1-TOLL)
   self.founder(w,day)
   # Sympatric actors behave independently, with resource contention and social learning.
   current=list(w.agents);w.rng.shuffle(current)
   for a in current:
    if not a.alive:continue
    self.maintenance(w,a,day)
    if not a.alive:continue
    if a.species in ('creation','castor'):
     self.creation_action(w,a,day)
     self.creation_reproduction(w,a,day)
    else:self.animal_step(w,a,day)
   self.animal_culture(w)
   self.institutions(w,day)
   if self.logs:
    humans=w.living('creation'); h=statistics.mean(a.hunger for a in humans) if humans else float('nan')
    need=[statistics.mean((100-a.hunger if i==0 else [0,a.safety,a.belong,a.esteem,a.purpose][i]) for a in humans) if humans else 0 for i in range(5)]
    self.rows.append({'day':day,'world':w.name,'daylight':round(w.daylight,3),'humans':len(humans),'herbivores':len(w.living('herbivore')),
      'predators':len(w.living('predator')),'scavengers':len(w.living('scavenger')),
      'plants':round(sum(p.stock['plant'][0] for p in w.patches.values()),3),'food':round(sum(p.stock['food'][0] for p in w.patches.values()),3),
      'detritus':round(sum(p.stock['detritus'][0]+p.stock['carcass'][0] for p in w.patches.values()),3),
      'goods':round(sum(p.stock['goods'][0] for p in w.patches.values()),3),'world_heat':round(sum(p.heat for p in w.patches.values()),3),'house':round(self.house,3),
      'underworld':round(sum(self.underworld),3),'avg_hunger':round(h,3),
      'physiological':round(need[0],3),'safety':round(need[1],3),'belonging':round(need[2],3),'esteem':round(need[3],3),'purpose':round(need[4],3),
      'institutions':len(w.institutions),'births':sum(w.births.values()),'deaths':sum(w.deaths.values()),
      'cumulative_toll':round(w.toll,3)})
  self.audit(day)
 def run(self):
  for day in range(1,self.days+1):self.day_step(day)
  res={'seed':self.seed,'days':self.days,'initial_energy':self.initial_energy,'final_energy':self.all_energy(),
      'wellspring_added':self.wellspring,'sunlight_emitted':self.sun_emitted,'returned_from_underworld':self.returned,
      'house_final':self.house,'underworld_final':sum(self.underworld),'energy_error_max':max(abs(x['energy_error']) for x in self.audits),
      'mass_error_max':max(abs(x['max_element_error']) for x in self.audits),'worlds':{}}
  for w in self.worlds:
   humans=w.living('creation');live=w.living()
   res['worlds'][w.name]={'daylight_final':w.daylight,'final_population':{sp:len(w.living(sp)) for sp in SPECIES},
     'births':dict(w.births),'deaths':dict(w.deaths),'plants_final':sum(p.stock['plant'][0] for p in w.patches.values()),
     'food_final':sum(p.stock['food'][0]+p.stock['stored'][0] for p in w.patches.values()),
     'goods_final':sum(p.stock['goods'][0] for p in w.patches.values()),
     'mean_hunger':statistics.mean(a.hunger for a in humans) if humans else None,
     'mean_health':statistics.mean(a.health for a in humans) if humans else None,
     'mean_belonging':statistics.mean(a.belong for a in humans) if humans else None,
     'mean_esteem':statistics.mean(a.esteem for a in humans) if humans else None,
     'mean_purpose':statistics.mean(a.purpose for a in humans) if humans else None,
     'nodes_total':sum(len(a.nodes) for a in live),'actors_with_nodes':sum(bool(a.nodes) for a in live),
     'institution_events':w.institution_events,'founder_history':w.founder_history,
     'decision_counts':dict(w.actions),'animal_action_counts':dict(w.animal_actions),
     'hunting_attempts':w.pred_hunts,'hunting_success':w.pred_wins,
     'hunting_rate':w.pred_wins/w.pred_hunts if w.pred_hunts else None,
     'migration_counts':dict(w.moves),'cultural_route_transmissions':w.migration_learns,
     'harvested':w.harvested,'total_toll':w.toll,'social_bonds':sum(len(a.friends) for a in humans)//2,
     'final_mass':w.mass_by_element(),'initial_mass':self.initial_mass[w.name],
     'final_world_energy':w.energy_total()}
  if self.logs:self.save(res)
  return res
 def save(self,res):
  for name,rows in [('founders_v012_turns.csv',self.rows),('founders_v012_events.csv',self.events),
                    ('founders_v012_births.csv',self.birth_events),('founders_v012_institutions.csv',sum((w.institution_events for w in self.worlds),[]))]:
   if not rows:continue
   with (OUT/name).open('w',newline='') as f:
    wr=csv.DictWriter(f,fieldnames=rows[0].keys());wr.writeheader();wr.writerows(rows)
  (OUT/'founders_v012_results.json').write_text(json.dumps(res,indent=2,allow_nan=False))

if __name__=='__main__':
 s=Simulation();summary=s.run();print(json.dumps(summary,indent=2))
