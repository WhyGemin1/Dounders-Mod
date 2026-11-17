import random,json,csv,math,collections
R=random.Random(19)
# All numeric settings are invented, not canonical.
# Material accounting: abstract kg of nutrient-bearing biomass and mineral pools.
class World:
 def __init__(self,name,policy):
  self.name=name;self.policy=policy;self.soil=800.;self.plants=300.;self.herbs=[{'age':R.randrange(1,12),'energy':8.,'hunger':0.} for _ in range(24)];self.preds=[{'age':R.randrange(2,18),'energy':12.,'hunger':0.} for _ in range(5)];self.scavs=[{'age':R.randrange(1,14),'energy':8.,'hunger':0.} for _ in range(4)];self.carcass=30.;self.inventory=40.;self.waste=30.;self.goods=0.;self.actors=[{'id':i,'food':3.,'mem':{},'events':[],'skills':collections.Counter(),'choice':collections.Counter(),'needs':{'hunger':R.uniform(0.25,0.7),'safety':R.uniform(.25,.7),'belonging':R.uniform(.2,.8),'esteem':R.uniform(.2,.8),'purpose':R.uniform(.2,.8)}} for i in range(6)];self.sun_store=0.;self.house_return=0.;self.energy_env=150.;self.energy_heat=0.;self.events=collections.Counter();self.log=[];self.born=collections.Counter();self.died=collections.Counter();self.extracted=0.;self.harvested=0.
 def mass(self):return self.soil+self.plants+sum(x['energy'] for x in self.herbs+self.preds+self.scavs)+self.carcass+self.inventory+self.waste+self.goods+sum(a['food'] for a in self.actors)
 def move(self,src,dst,amount):
  q=min(max(0,amount),getattr(self,src));setattr(self,src,getattr(self,src)-q);setattr(self,dst,getattr(self,dst)+q);return q
 def step(self,t,sun):
  self.energy_env+=sun;self.sun_store+=sun
  # Plant growth uses both environmental energy and soil mass, no mass creation.
  growth=min(self.soil, max(0, (14 if self.policy=='regenerative' else 11)* (0.65+0.35*math.sin(t/9)**2)),self.energy_env*.8)
  self.move('soil','plants',growth);self.energy_env-=growth*.5;self.energy_heat+=growth*.5
  # Herbivores: each consumes plant mass, transfers into body or waste; body energy used as biomass proxy.
  for a in list(self.herbs):
   a['age']+=1;a['hunger']+=1;eat=min(self.plants,2.8);self.plants-=eat;a['energy']+=eat*.38;self.waste+=eat*.62
   a['energy']-=.55;self.waste+=.55
   if eat<1.5:a['hunger']+=1
   else:a['hunger']=max(0,a['hunger']-1)
   if a['energy']<2 or a['age']>35 or a['hunger']>6:
    self.herbs.remove(a);self.carcass+=max(0,a['energy']);self.died['herbivore']+=1;continue
   if a['age']>5 and a['energy']>12 and len(self.herbs)<90 and R.random()<.075:
    a['energy']-=4;self.herbs.append({'age':0,'energy':4.,'hunger':0});self.born['herbivore']+=1
  # Predators: limited by hunt encounter, maturity and gestation surrogate.
  for a in list(self.preds):
   a['age']+=1;a['hunger']+=1
   if self.herbs and R.random()<min(.65,len(self.herbs)/30):
    prey=self.herbs.pop(R.randrange(len(self.herbs)));self.died['predation']+=1
    gain=prey['energy'];a['energy']+=gain*.65;self.carcass+=gain*.35;a['hunger']=0
   a['energy']-=.8;self.waste+=.8
   if a['energy']<2 or a['age']>48 or a['hunger']>10:
    self.preds.remove(a);self.carcass+=max(0,a['energy']);self.died['predator']+=1;continue
   if a['age']>10 and a['energy']>22 and len(self.preds)<18 and R.random()<.028:
    a['energy']-=7;self.preds.append({'age':0,'energy':7.,'hunger':0});self.born['predator']+=1
  for a in list(self.scavs):
   a['age']+=1;a['hunger']+=1
   eat=min(self.carcass,2.);self.carcass-=eat;a['energy']+=eat*.4;self.waste+=eat*.6
   a['energy']-=.45;self.waste+=.45
   if eat>.5:a['hunger']=0
   if a['energy']<1 or a['age']>35 or a['hunger']>9:
    self.scavs.remove(a);self.carcass+=max(0,a['energy']);self.died['scavenger']+=1;continue
   if a['age']>7 and a['energy']>11 and len(self.scavs)<25 and R.random()<.035:
    a['energy']-=3;self.scavs.append({'age':0,'energy':3.,'hunger':0});self.born['scavenger']+=1
  # decomposition: detritus and waste into soil, energy cost and toll, all accounted.
  rate=.34 if self.policy=='regenerative' else .07
  dec=min(self.carcass,4*rate);self.move('carcass','soil',dec)
  self.move('waste','soil',min(self.waste,9*rate))
  # 6 autonomous actors: softmax choices based on needs, imperfect memory, and perceived action outcomes.
  for a in self.actors:
   a['needs']['hunger']=min(1,a['needs']['hunger']+.10)
   a['needs']['safety']=min(1,a['needs']['safety']+.012)
   a['needs']['belonging']=min(1,a['needs']['belonging']+.016)
   a['needs']['esteem']=min(1,a['needs']['esteem']+.014)
   a['needs']['purpose']=min(1,a['needs']['purpose']+.018)
   effects={'eat':{'hunger':-.55},'harvest':{'hunger':-.04,'safety':-.06},'recycle':{'safety':-.12,'purpose':-.09},'socialize':{'belonging':-.40,'safety':-.04},'research':{'purpose':-.34,'esteem':-.14},'protect':{'safety':-.38,'esteem':-.09},'build':{'safety':-.22,'esteem':-.18}}
   feasible=['socialize','research','protect']
   if self.inventory>=1:feasible+=['eat','build']
   if self.plants>=2:feasible+=['harvest']
   if self.waste>=2:feasible+=['recycle']
   scores={}
   for act in feasible:
    score=sum(-d*a['needs'][n] for n,d in effects[act].items())*10
    score+=a['mem'].get(act,0)*1.3
    score+=R.uniform(-.7,.7)
    if act=='harvest' and self.inventory<12:score+=2
    if act=='recycle' and self.policy=='regenerative':score+=2.2
    if act=='build' and self.policy=='extractive':score+=1.8
    scores[act]=score
   top=max(scores.values());weights=[math.exp((scores[x]-top)/1.2) for x in feasible];choice=R.choices(feasible,weights)[0];a['choice'][choice]+=1;self.events[choice]+=1
   success=True
   if choice=='eat':
    q=self.move('inventory','waste',0) # actual consumption below, not double-count
    q=min(self.inventory,1.7);self.inventory-=q;a['food']+=q*.5;self.waste+=q*.5;a['needs']['hunger']=max(0,a['needs']['hunger']-.55)
   elif choice=='harvest':
    q=self.move('plants','inventory',min(2.8,self.plants));self.harvested+=q
    success=q>0
   elif choice=='recycle':
    q=self.move('waste','soil',min(2.5,self.waste));success=q>0
   elif choice=='build':
    q=self.move('inventory','goods',min(1.2,self.inventory));success=q>0
   else:pass
   # All actors' own biological food reserve metabolizes into waste (mass conserved).
   consumed=min(a['food'],.42);a['food']-=consumed;self.waste+=consumed
   if a['food']<.2:a['needs']['hunger']=min(1,a['needs']['hunger']+.18)
   for n,d in effects[choice].items():
    if n!='hunger' or choice!='eat':a['needs'][n]=max(0,min(1,a['needs'][n]+d))
   # memory reward is experience-based; tracks outcome and adjusts expectation
   reward=(1 if success else -1);a['mem'][choice]=.86*a['mem'].get(choice,0)+.14*reward
   a['events'].append((t,choice,success));a['skills'][choice]+=(1 if success else .15)
  # Net environmental energy circulation: all spent energy transfers to house/world/underworld, no loss.
  # Here sunlight and returned energy are tracked as separate energy ledger, without pretending biomass=EU.
  spent=min(self.energy_env,3.5+len(self.herbs)*.06+len(self.preds)*.15)
  self.energy_env-=spent;self.house_return+=spent*.65;self.energy_env+=spent*.20 # world share
  # 15% goes to an Underworld transit account, returned by external scheduler.
  self.under_in=spent*.15
  self.log.append({'turn':t,'world':self.name,'mass':self.mass(),'soil':self.soil,'plants':self.plants,'herbivores':len(self.herbs),'predators':len(self.preds),'scavengers':len(self.scavs),'inventory':self.inventory,'goods':self.goods,'waste':self.waste,'carcass':self.carcass,'sun':sun,'energy_env':self.energy_env,'house_return':self.house_return})

w1=World('Extraction','extractive');w2=World('Regeneration','regenerative')
initial=w1.mass();assert abs(w2.mass()-initial)<1e-8
house=10000.;well_total=0.;sun_total=0.;under=[0.]*10;in_transit=0.;energy_initial=house+w1.energy_env+w2.energy_env
house_history=[]
for t in range(1,121):
 well=18.;house+=well;well_total+=well
 # One-layer-per-turn transport; 8 EU throughput per link.
 transfer=min(under[-1],8.);under[-1]-=transfer;house+=transfer
 for i in range(8,-1,-1):
  transfer=min(under[i],8.,max(0,50.-under[i+1]));under[i]-=transfer;under[i+1]+=transfer
 # Sunlight minimum plus proportional inflow, divided equally between worlds.
 incoming=well+sum(w.house_return for w in (w1,w2))*.0 # returned energy added below as current-turn flow
 sunlight=min(house,12+0.35*well);house-=sunlight;sun_total+=sunlight
 for w in (w1,w2):
  before=w.house_return
  w.step(t,sunlight/2)
  delta=w.house_return-before
  house+=delta
  under[0]+=w.under_in
 # log reserves
 house_history.append({'turn':t,'house':house,'underworld':sum(under),'total_energy':house+sum(under)+w1.energy_env+w2.energy_env+w1.energy_heat+w2.energy_heat})
# Energy ledger does not yet track spent work committed to actor biomass and other processes;
# environmental energy only, and toll shares are transferred correctly for this modeled subledger.
# 15% of spent energy to Underworld, 65% to House, 20% to environment.
final_energy=house+sum(under)+w1.energy_env+w2.energy_env+w1.energy_heat+w2.energy_heat
summary={'assumptions':'All numbers invented. 120 turns; abstract kg material stocks; population agents/cohorts; environmental energy separate from biomass proxy.', 'mass_initial_each':initial,'worlds':{},'energy_initial':energy_initial,'wellspring_added':well_total,'energy_final':final_energy,'energy_error':final_energy-(energy_initial+well_total),'sunlight_total':sun_total,'house_final':house,'environmental_heat':w1.energy_heat+w2.energy_heat,'underworld_final':sum(under)}
for w in (w1,w2):
 summary['worlds'][w.name]={'final_mass':w.mass(),'mass_error':w.mass()-initial,'soil':w.soil,'plants':w.plants,'herbivores':len(w.herbs),'predators':len(w.preds),'scavengers':len(w.scavs),'food_inventory':w.inventory,'goods':w.goods,'births':dict(w.born),'deaths':dict(w.died),'actions':dict(w.events),'harvested':w.harvested,'distinct_actions_per_actor':[len(a['choice']) for a in w.actors],'avg_mem':{k:sum(a['mem'].get(k,0) for a in w.actors)/6 for k in ('harvest','recycle','build','research')}}
with open('/mnt/data/founders_v09_results.json','w') as f:json.dump(summary,f,indent=2)
with open('/mnt/data/founders_v09_turns.csv','w',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=w1.log[0].keys());writer.writeheader();writer.writerows(w1.log+w2.log)
with open('/mnt/data/founders_v09_actor_events.csv','w',newline='') as f:
 wr=csv.writer(f);wr.writerow(['world','actor','turn','action','success'])
 for w in (w1,w2):
  for a in w.actors:
   for ev in a['events']:wr.writerow([w.name,a['id'],*ev])
print(json.dumps(summary,indent=2))
