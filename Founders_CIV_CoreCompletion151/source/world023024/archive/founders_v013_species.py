"""Founders-CIV v0.13: species-resolved ecological extension of v0.12.
Experiment: baseline, energy-only, learned-strategies-only, combined.
All values are toy parameters. Python 3.10+, standard library only.
Run: python /mnt/data/founders_v013_species.py
"""
from __future__ import annotations
import csv, json, random, math, statistics, collections, sys, copy
from pathlib import Path
import founders_v012 as base
OUT=Path(__file__).resolve().parent/'outputs'
DAYS=180
SEEDS=[12011,12043,12071]
HERBS={'grass_grazer','forest_browser'}
PREDS={'pack_hound','shadow_stalker'}
SCAVS={'carrion_bird','ground_scavenger'}
DECOMPS={'soil_fungus'}
ANIMALS=HERBS|PREDS|SCAVS|DECOMPS

SPECIES_PROFILE={
 'grass_grazer':{'max_age':720,'maturity':55,'base_burn':.16,'capacity':13,'adult_mass':1.65,'fertility':.034,'gestation':19,
       'habitat':'grassland','strategy':'grazing + learned migration','special':['navigate','evade','graze']},
 'forest_browser':{'max_age':820,'maturity':70,'base_burn':.15,'capacity':14,'adult_mass':1.8,'fertility':.027,'gestation':24,
       'habitat':'forest','strategy':'browse and cover-seeking','special':['browse','cover_use','evade']},
 'pack_hound':{'max_age':860,'maturity':90,'base_burn':.045,'capacity':38,'adult_mass':2.7,'fertility':.020,'gestation':34,
       'habitat':'grassland','strategy':'social tracking and coordinated pursuit','special':['track','coordinate','hunt']},
 'shadow_stalker':{'max_age':850,'maturity':100,'base_burn':.05,'capacity':36,'adult_mass':2.7,'fertility':.016,'gestation':38,
       'habitat':'forest','strategy':'solitary stalk and grapple','special':['sneak','grapple','hunt']},
 'carrion_bird':{'max_age':660,'maturity':65,'base_burn':.055,'capacity':21,'adult_mass':1.4,'fertility':.022,'gestation':28,
       'habitat':'ridge','strategy':'wide-range carcass detection','special':['spot_carrion','migration','scavenge']},
 'ground_scavenger':{'max_age':690,'maturity':70,'base_burn':.065,'capacity':19,'adult_mass':1.4,'fertility':.028,'gestation':29,
       'habitat':'wetland','strategy':'scent tracking and carcass utilization','special':['track','scavenge']},
 'soil_fungus':{'max_age':900,'maturity':45,'base_burn':.008,'capacity':8,'adult_mass':.40,'fertility':.026,'gestation':16,
       'habitat':'forest','strategy':'decomposition and nutrient cycling','special':['decompose','humidity_sense']},
}
SKILLS=['track','coordinate','sneak','grapple','graze','browse','cover_use','evade','scavenge','spot_carrion','decompose','humidity_sense']

class Sim(base.Simulation):
 def __init__(self,mode='combined',seed=12011,days=DAYS,logs=False,fix_migration=True):
  if mode not in {'baseline','energy_only','strategies_only','combined'}:raise ValueError(mode)
  self.mode=mode;self.fix_migration=fix_migration
  # Each instance owns its own species config: no cross-run global mutation.
  species=copy.deepcopy(base.SPECIES)
  for sp,profile in SPECIES_PROFILE.items():species[sp]=copy.deepcopy(profile)
  efficient=mode in ('energy_only','combined')
  if not efficient:
   for sp in sorted(PREDS):
    species[sp]['base_burn']=.085
    species[sp]['capacity']=16.
  super().__init__(seed=seed,days=days,logs=False,species=species)
  self.logs=logs
  self.animal_events=[];self.predator_daily=[]
  for w in self.worlds:
   herbs=[a for a in w.agents if a.species=='herbivore']
   preds=[a for a in w.agents if a.species=='predator']
   scavs=[a for a in w.agents if a.species=='scavenger']
   for i,a in enumerate(herbs):
    a.species='grass_grazer' if i%3!=0 else 'forest_browser'
   for i,a in enumerate(preds):
    a.species='pack_hound' if i<2 else 'shadow_stalker'
    a.patch='grassland' if i<2 else 'forest'
    a.sex='F' if i%2==0 else 'M'
   for i,a in enumerate(scavs):a.species='carrion_bird' if i<4 else 'ground_scavenger'
   for a in herbs+preds+scavs:
    a.skill.update({skill:w.rng.uniform(.15,.47) for skill in SKILLS})
    a.belief.update({skill:0. for skill in SKILLS})
    if a.species=='shadow_stalker':a.skill['sneak']+=.14;a.skill['grapple']+=.08
    if a.species=='pack_hound':a.skill['coordinate']+=.13
   # Actual founding of decomposer life uses explicit detritus as its source (not free matter).
   for p in w.patches.values():
    a=w.spawn('soil_fungus',p.name,adult=True,age=62)
    source=p.stock['detritus'];mass=a.body_mass;energy=a.body_energy
    if source[0]<mass or source[1]<energy:raise ValueError('not enough detrital matter to seed fungi')
    source[0]-=mass;source[1]-=energy
    # Fungus energy reserve is taken from founder's reserve: a transfer, not a new source.
    if w.founder_reserve<a.reserve:raise ValueError('insufficient fungus reserve funding')
    w.founder_reserve-=a.reserve
    a.skill.update({s:w.rng.uniform(.15,.47) for s in SKILLS})
    a.belief.update({s:0. for s in SKILLS})
   # Seed reserves by moving energy from the House. Control has identical TOTAL available energy.
   for a in preds:
    if efficient:
     additional=max(0,self.species[a.species]['capacity']*.75-a.reserve)
     a.reserve+=additional;self.house-=additional
    else:
     over=max(0,a.reserve-self.species[a.species]['capacity'])
     if over:a.reserve-=over;self.house+=over
   w._index_dirty=True
   w.hunt_attempts=collections.Counter();w.hunt_wins=collections.Counter()
   w.hunt_participants=collections.Counter();w.packs_hunts=0;w.ambush_hunts=0
   w.learned_hunts=0;w.animal_births=collections.Counter()
   w.completed_hunt_turn=set()
   w.initial_mass=w.mass_by_element();w.initial_energy=w.energy_total()
  # shared totals captured after all transfers; compare controls from matched initial conditions.
  self.initial_energy=self.all_energy()
  self.initial_mass={w.name:w.mass_by_element() for w in self.worlds}

 def spend(self,w,a,cost,state=True):
  return super().spend(w,a,cost,state)

 def maintenance(self,w,a,day):
  # Biological aging and maintenance remain in base class; high hunger with full fuel should
  # not produce instantaneous starvation. Hunger still matters for learned decisions.
  super().maintenance(w,a,day)
  # Large accessible reserves prevent metabolic starvation; hunger remains a drive to hunt.
  if a.alive and a.species in PREDS and a.reserve>self.species[a.species]['capacity']*.35:
   if a.hunger>83:a.health=min(100,a.health+.9)
   a.hunger=min(a.hunger,82.)

 def migration(self,w,a,day):
  if a.species in ('creation','castor'):return super().migration(w,a,day)
  if a.species in DECOMPS:return False
  p=w.patches[a.patch]
  destinations=base.PATCHES if a.species=='carrion_bird' else base.ADJ[a.patch]
  scores=[]
  for d in destinations:
   if d==a.patch:continue
   dest=w.patches[d]
   if a.species in HERBS:
    resource=dest.stock['plant'][0]
    threat=len(w.present(d,PREDS))
    habitat=1.0 if d==SPECIES_PROFILE[a.species]['habitat'] else 0.
    score=.6*math.log1p(resource)-.35*threat+.55*habitat+a.route_value.get(d,0)
   elif a.species in PREDS:
    resource=len(w.present(d,HERBS))
    score=.75*math.log1p(resource)+a.route_value.get(d,0)
    if a.species=='shadow_stalker':score+=.3*dest.cover
   else:
    resource=dest.stock['carcass'][0];score=.9*math.log1p(resource)+a.route_value.get(d,0)
   score+=w.rng.gauss(0,.18)
   scores.append((score,d))
  if not scores:return False
  _,d=max(scores)
  if not self.spend(w,a,.10):return False
  a.patch=d;w._index_dirty=True;w.moves[a.species]+=1
  if self.fix_migration:
   if a.species in HERBS:dest_resource=w.patches[d].stock['plant'][0]
   elif a.species in PREDS:dest_resource=len(w.present(d,HERBS))
   else:dest_resource=w.patches[d].stock['carcass'][0]
  else:dest_resource=resource # exact legacy behavior retained for golden comparisons
  a.route_value[d]=.9*a.route_value.get(d,0)+.1*(1 if dest_resource>1 else -1)
  self.experience(w,a,'migration',day,True,reward=.2,context=d)
  return True

 def experience(self,w,a,action,day,success,reward=0,context=''):
  super().experience(w,a,action,day,success,reward,context)
  if a.species in ANIMALS and self.logs and (action in ('hunt','coordinate','sneak','grapple','decompose','migration','graze','browse')):
   self.animal_events.append({'day':day,'world':w.name,'actor':a.uid,'species':a.species,'patch':a.patch,'action':action,'success':int(success),
     'skill':round(a.skill.get(action,0),4),'reserve':round(a.reserve,3),'context':context})

 def decomposition_step(self,w,a,day):
  p=w.patches[a.patch];src=p.stock['detritus']
  if src[0]<.08 or src[1]<.01:
   self.experience(w,a,'decompose',day,False);return
  q=min(src[0],.16+.25*a.skill['decompose'])
  ratio=q/src[0];en=src[1]*ratio
  src[0]-=q;src[1]-=en
  for k,part in base.ELEMENTS.items():p.env[k]+=q*part
  # Organics->inorganic decomposition is a material-state change; toll on released energy.
  toll=en*base.TOLL
  self.toll(w,p,toll)
  gain=min(en*.50,self.species[a.species]['capacity']-a.reserve)
  a.reserve+=gain
  # A small portion of decaying material becomes new fungal tissue. It has to be
  # funded by material and energy from the same detrital source.
  biomass=min(q*.045,max(0.,self.species[a.species]['adult_mass']*1.35-a.body_mass),max(0.,(en-toll-gain)/3.))
  a.body_mass+=biomass;a.body_energy+=3*biomass
  for k,part in base.ELEMENTS.items():p.env[k]-=biomass*part
  p.heat+=en-toll-gain-3*biomass
  self.experience(w,a,'decompose',day,True,reward=.4)
  w.animal_actions['decompose']+=1

 def predator_hunt(self,w,a,day):
  prey=list(w.present(a.patch,HERBS))
  if not prey:
   self.migration(w,a,day)
   return
  if a.species=='pack_hound':
   if a.uid in w.completed_hunt_turn:return
   pack=[x for x in w.present(a.patch,'pack_hound') if x.uid not in w.completed_hunt_turn]
   members=sorted(pack,key=lambda x:x.skill['coordinate']+x.skill['hunt'],reverse=True)[:4]
   if not members:return
   if self.mode in ('baseline','energy_only'):members=[a]  # solo, no coordinated learning
   w.completed_hunt_turn.update(x.uid for x in members)
   target=w.rng.choice(prey)
   avg_coord=statistics.mean(x.skill['coordinate'] for x in members)
   avg_hunt=statistics.mean(x.skill['hunt'] for x in members)
   prey_evasion=target.skill['evade']
   if self.mode in ('baseline','energy_only'):
    prob=.055+.10*a.skill['hunt']-.055*prey_evasion
   else:
    # Coordination increases up to 4 active hunters; group free-riding would cap gains.
    prob=.065+.16*avg_hunt+.32*min(3,len(members)-1)*avg_coord-.05*prey_evasion
   prob=max(.025,min(.31,prob))
   # Search is not guaranteed to find prey merely because prey inhabit the patch.
   encounter=1-math.exp(-len(prey)/5.5)
   if w.rng.random()>encounter:
    for x in members:self.spend(w,x,.027)
    w.animal_actions['search_no_encounter']+=1
    return
   cost=(.17 if self.mode in ('baseline','strategies_only') else .085)
   participants=[]
   for x in members:
    if self.spend(w,x,cost):participants.append(x)
   if not participants:return
   w.hunt_attempts['pack_hound']+=1;w.hunt_participants['pack_hound']+=len(participants)
   ok=w.rng.random()<prob
   if ok:
    w.hunt_wins['pack_hound']+=1
    self.die(w,target,'pack_hunted')
    # Every pack member is able to feed from THE SAME finite carcass stock.
    for x in sorted(participants,key=lambda z:z.reserve):
     if w.patches[a.patch].stock['carcass'][0]>.05:
      self.action_consume(w,x,'carcass',min(1.,1.8/len(participants)),day)
      x.hunger=max(0.,x.hunger-18.)
   else:self.experience(w,target,'evade',day,True,context='escaped-pack')
   for x in participants:
    self.experience(w,x,'hunt',day,ok,reward=.9 if ok else .05,context=f'pack={len(participants)};chance={prob:.3f}')
    if self.mode in ('strategies_only','combined'):
     self.experience(w,x,'coordinate',day,ok,reward=.5,context='joint-hunt')
   if ok and len(members)>1:w.learned_hunts+=1
   w.animal_actions['pack_hunt']+=1
  else:
   target=w.rng.choice(prey)
   if not self.spend(w,a,.13 if self.mode in ('baseline','strategies_only') else .075):return
   p=w.patches[a.patch]
   if self.mode in ('baseline','energy_only'):
    chance=.06+.11*a.skill['hunt']-.07*target.skill['evade']
    stealth_ok=True
   else:
    stealth_prob=min(.88,.50+.34*a.skill['sneak']*p.cover-.22*target.skill['evade'])
    stealth_ok=w.rng.random()<stealth_prob
    grapple_prob=min(.75,.18+.37*a.skill['grapple']+.17*a.skill['hunt']-.18*target.skill['evade'])
    chance=stealth_prob*grapple_prob
   chance=max(.015,min(.34,chance))
   if w.rng.random()>1-math.exp(-len(prey)/5.5):
    self.experience(w,a,'track',day,False,context='prey-not-located')
    w.animal_actions['search_no_encounter']+=1
    return
   w.hunt_attempts['shadow_stalker']+=1
   ok=(w.rng.random()<chance) if self.mode in ('baseline','energy_only') else (stealth_ok and w.rng.random()<max(.02,min(.72,.18+.37*a.skill['grapple']+.17*a.skill['hunt']-.18*target.skill['evade'])))
   if ok:
    w.hunt_wins['shadow_stalker']+=1
    self.die(w,target,'ambush_hunted')
    self.action_consume(w,a,'carcass',min(1.65,w.patches[a.patch].stock['carcass'][0]),day)
    a.hunger=max(0.,a.hunger-25.)
   else:self.experience(w,target,'evade',day,True,context='escaped-ambush')
   self.experience(w,a,'hunt',day,ok,reward=.65 if ok else .04,context=f'ambush_p={chance:.3f}')
   if self.mode in ('strategies_only','combined'):
    self.experience(w,a,'sneak',day,stealth_ok,reward=.25)
    self.experience(w,a,'grapple',day,ok,reward=.35)
   w.animal_actions['ambush_hunt']+=1

 def animal_step(self,w,a,day):
  p=w.patches[a.patch];sp=self.species[a.species];rng=w.rng
  a.hunger=min(100,a.hunger+.45)
  if a.species in HERBS:
   preferred=SPECIES_PROFILE[a.species]['habitat']
   if p.stock['plant'][0]>3 and (a.reserve<sp['capacity']*.85 or a.hunger>58):
    if self.spend(w,a,.08):
     action='graze' if a.species=='grass_grazer' else 'browse'
     ok,q=self.action_consume(w,a,'plant',rng.uniform(.23,.37),day)
     a.skill[action]=min(1.5,a.skill[action]+.003 if ok else a.skill[action])
     self.experience(w,a,action,day,ok,reward=q)
     w.animal_actions[action]+=1
   elif p.stock['plant'][0]<6 or a.reserve<2:
    self.migration(w,a,day)
   else:w.animal_actions['rest_herb']+=1
   if rng.random()<.07:a.skill['evade']=min(1.5,a.skill['evade']+.003)
  elif a.species in PREDS:
   carcass=p.stock['carcass'][0]
   # Replenish from carrion only if hungry enough to justify a feeding event.
   if carcass>.15 and (a.hunger>24 or a.reserve<sp['capacity']*.72):
    self.action_consume(w,a,'carcass',min(carcass,rng.uniform(.65,1.25)),day)
    a.hunger=max(0.,a.hunger-20.)
    w.animal_actions['predator_scavenge']+=1
   elif a.reserve<sp['capacity']*.48 or a.hunger>65:
    self.predator_hunt(w,a,day)
   else:w.animal_actions['predator_rest']+=1
  elif a.species in SCAVS:
   if p.stock['carcass'][0]>.12 and (a.reserve<sp['capacity']*.84 or a.hunger>35):
    self.action_consume(w,a,'carcass',rng.uniform(.32,.65),day)
    self.experience(w,a,'scavenge',day,True,reward=.3)
    w.animal_actions['scavenger_feed']+=1
   elif p.stock['plant'][0]>.3 and a.species=='ground_scavenger' and a.reserve<sp['capacity']*.8:
    self.action_consume(w,a,'plant',min(.2,p.stock['plant'][0]),day)
    w.animal_actions['detritivore']+=1
   elif a.reserve<sp['capacity']*.65 or a.hunger>50:self.migration(w,a,day)
   else:w.animal_actions['scavenger_rest']+=1
  else:
   self.decomposition_step(w,a,day)
  # Reproduction requires sex, maturity, access to partner, adequate body reserves, and a gestation period.
  if a.age>=sp['maturity'] and a.reproductive_cooldown==0 and (a.sex=='F' or a.species in DECOMPS):
   partners=[x for x in w.present(a.patch,a.species) if x.uid!=a.uid and x.sex=='M' and x.age>=sp['maturity']]
   if (partners or a.species in DECOMPS) and a.reserve>sp['capacity']*.36 and a.body_mass>sp['adult_mass']*.78:
    if a.pregnancy==0 and rng.random()<sp['fertility']:a.pregnancy=sp['gestation']
  if a.pregnancy>0:
   a.pregnancy-=1
   if a.pregnancy==0 and a.alive and a.body_mass>sp['adult_mass']*.67:
    child=w.spawn(a.species,a.patch,adult=False,mother=a)
    if child:
     child.skill.update({key:.075 for key in SKILLS})
     a.reproductive_cooldown=sp['gestation']*2
     w.animal_births[a.species]+=1
     if self.logs:self.birth_events.append({'day':day,'world':w.name,'mother':a.uid,'baby':child.uid,'species':a.species})

 def animal_culture(self,w):
  for p in base.PATCHES:
   for sp in sorted(ANIMALS-DECOMPS):
    group=list(w.present(p,sp))
    if len(group)<2:continue
    mentor=max(group,key=lambda x:x.skill.get('hunt',0)+x.skill.get('coordinate',0)+x.route_value.get(p,0))
    learner=w.rng.choice(group)
    if learner.uid==mentor.uid:continue
    learner.route_value[p]+=.09*(mentor.route_value.get(p,0)-learner.route_value.get(p,0))
    if self.mode in ('strategies_only','combined') and sp in PREDS:
     skill='coordinate' if sp=='pack_hound' else 'sneak'
     if mentor.skill[skill]>learner.skill[skill]+.06:
      learner.skill[skill]+=.02*(mentor.skill[skill]-learner.skill[skill])
      w.migration_learns+=1

 def decay(self,w,p):
  # Background abiotic transformation is slower, fungi actively recycle detritus.
  for stock,rate in [('detritus',.020),('carcass',.050),('goods',.002),('food',.018),('stored',.006)]:
   m=p.stock[stock][0];q=min(m,m*rate)
   if q<=0:continue
   if stock in ('goods','food','stored','carcass'):p.move(stock,'detritus',q)
   else:
    en=p.stock[stock][1]*(q/m);p.stock[stock][0]-=q;p.stock[stock][1]-=en
    for k,f in base.ELEMENTS.items():p.env[k]+=q*f
    toll=en*base.TOLL;self.toll(w,p,toll);p.heat+=en-toll

 def day_step(self,day):
  for w in self.worlds:w.completed_hunt_turn=set()
  super().day_step(day)
  if self.logs:
   for row in self.rows[-len(self.worlds):]:
    w=next(x for x in self.worlds if x.name==row['world'])
    row['herbivores']=sum(len(w.living(sp)) for sp in sorted(HERBS))
    row['predators']=sum(len(w.living(sp)) for sp in sorted(PREDS))
    row['scavengers']=sum(len(w.living(sp)) for sp in sorted(SCAVS))
    row['decomposers']=sum(len(w.living(sp)) for sp in sorted(DECOMPS))
  if self.logs:
   for w in self.worlds:
    self.predator_daily.append({'day':day,'world':w.name,
      **{f'n_{s}':len(w.living(s)) for s in SPECIES_PROFILE},
      **{f'attempt_{s}':w.hunt_attempts[s] for s in sorted(PREDS)},
      **{f'wins_{s}':w.hunt_wins[s] for s in sorted(PREDS)},
      'plant_mass':round(sum(p.stock['plant'][0] for p in w.patches.values()),3),
      'carcass_mass':round(sum(p.stock['carcass'][0] for p in w.patches.values()),3)})

 def save(self,res):
  # Save inherited action logs under v013 rather than overwriting original v012 files.
  for filename,rows in [('founders_v013_turns.csv',self.rows),('founders_v013_actor_events.csv',self.events),
                        ('founders_v013_births.csv',self.birth_events),('founders_v013_institutions.csv',sum((w.institution_events for w in self.worlds),[]))]:
   if not rows:continue
   with (OUT/filename).open('w',newline='') as f:
    wr=csv.DictWriter(f,fieldnames=rows[0].keys());wr.writeheader();wr.writerows(rows)

 def run(self):
  result=super().run()
  result['mode']=self.mode
  for w in self.worlds:
   x=result['worlds'][w.name]
   x['species_counts']={s:len(w.living(s)) for s in SPECIES_PROFILE}
   x['final_population']={'creation':len(w.living('creation')),'castor':len(w.living('castor')),
      'herbivores':sum(len(w.living(sp)) for sp in sorted(HERBS)),
      'predators':sum(len(w.living(sp)) for sp in sorted(PREDS)),
      'scavengers':sum(len(w.living(sp)) for sp in sorted(SCAVS)),
      'decomposers':sum(len(w.living(sp)) for sp in sorted(DECOMPS))}
   x['species_births']={s:int(w.animal_births[s]) for s in SPECIES_PROFILE}
   x['species_deaths']={s:int(w.deaths[s]) for s in SPECIES_PROFILE}
   x['species_hunts']={s:{'attempts':int(w.hunt_attempts[s]),'wins':int(w.hunt_wins[s]),
      'success_rate':w.hunt_wins[s]/w.hunt_attempts[s] if w.hunt_attempts[s] else None} for s in sorted(PREDS)}
   x['hunter_skill_means']={s:{skill:statistics.mean(a.skill.get(skill,0) for a in w.living(s)) if w.living(s) else None
         for skill in SPECIES_PROFILE[s]['special']} for s in sorted(PREDS)}
  if self.logs:
   for name,rows in [('founders_v013_predator_daily.csv',self.predator_daily),('founders_v013_animal_events.csv',self.animal_events)]:
    if rows:
     with (OUT/name).open('w',newline='') as f:
      ww=csv.DictWriter(f,fieldnames=rows[0].keys());ww.writeheader();ww.writerows(rows)
   (OUT/'founders_v013_detailed.json').write_text(json.dumps(result,indent=2))
  return result

def main():
 runs=[]
 for mode in ['baseline','energy_only','strategies_only','combined']:
  for seed in SEEDS:
   sim=Sim(mode,seed,DAYS,logs=(mode=='combined' and seed==SEEDS[0]))
   r=sim.run()
   for name,w in r['worlds'].items():
    pred=sum(w['species_counts'][k] for k in sorted(PREDS))
    prey=sum(w['species_counts'][k] for k in sorted(HERBS))
    d={'mode':mode,'seed':seed,'world':name,'predators':pred,'prey':prey,
      'scavengers':sum(w['species_counts'][k] for k in sorted(SCAVS)),'decomposers':w['species_counts']['soil_fungus'],
      'predator_births':sum(w['species_births'][k] for k in sorted(PREDS)),
      'predator_deaths':sum(w['species_deaths'][k] for k in sorted(PREDS)),
      'pack_attempts':w['species_hunts']['pack_hound']['attempts'],'pack_wins':w['species_hunts']['pack_hound']['wins'],
      'ambush_attempts':w['species_hunts']['shadow_stalker']['attempts'],'ambush_wins':w['species_hunts']['shadow_stalker']['wins'],
      'plants':round(w['plants_final'],2),'mass_error':r['mass_error_max'],'energy_error':r['energy_error_max']}
    runs.append(d)
   print('completed',mode,seed,'predators',[(name, sum(w['species_counts'][k] for k in sorted(PREDS))) for name,w in r['worlds'].items()],flush=True)
 with (OUT/'founders_v013_ablations.csv').open('w',newline='') as f:
  wr=csv.DictWriter(f,fieldnames=runs[0].keys());wr.writeheader();wr.writerows(runs)
 bymode={}
 for mode in ['baseline','energy_only','strategies_only','combined']:
  rr=[x for x in runs if x['mode']==mode]
  bymode[mode]={k:round(statistics.mean(x[k] for x in rr),4) for k in ['predators','prey','scavengers','decomposers','predator_births','predator_deaths','pack_attempts','pack_wins','ambush_attempts','ambush_wins','plants']}
  bymode[mode]['predator_persistence_fraction']=sum(x['predators']>0 for x in rr)/len(rr)
  bymode[mode]['max_mass_error']=max(x['mass_error'] for x in rr)
  bymode[mode]['max_energy_error']=max(x['energy_error'] for x in rr)
 summary={'days':DAYS,'seeds':SEEDS,'worlds_per_seed':2,'initial_predators_per_world':4,
  'design':'Ablation compares reserve+metabolism vs strategy+learning; same species initial populations; daylight policies as in v012',
  'modes':bymode,'individual_results':runs}
 (OUT/'founders_v013_comparison.json').write_text(json.dumps(summary,indent=2))
 print(json.dumps(bymode,indent=2),flush=True)

if __name__=='__main__':main()
