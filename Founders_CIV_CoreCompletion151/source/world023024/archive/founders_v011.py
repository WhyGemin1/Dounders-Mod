import random,csv,json,collections,statistics
SEED=11907; DAYS=180; N=24
ACTIONS=['eat','rest','farm','forage','build','socialize','help','train','explore','guard','store']
# Illustrative, dimensionless energy and mass units; all values experimental.
class World:
 def __init__(self,name,daylight):
  self.name=name;self.daylight=daylight;self.plants=440.;self.soil=1000.;self.food=130.;self.shelter=40.;self.stored=10.;self.harvested=0.;self.sun_received=0.;self.toll=0.;self.decisions=collections.Counter();self.history=[]
  self.agents=[Agent(i,SEED+i) for i in range(N)]
class Agent:
 def __init__(self,i,seed):
  r=random.Random(seed);self.i=i;self.energy=65.;self.hunger=20.;self.fatigue=20.;self.safety=55.;self.belong=45.;self.esteem=35.;self.purpose=35.;self.health=100.;self.skill={a:r.uniform(0.1,0.5) for a in ACTIONS};self.bias={a:r.uniform(-4,4) for a in ACTIONS};self.mem=collections.defaultdict(float);self.count=collections.Counter();self.friends=set();self.events=[];self.alive=True
 def choose(self,w,rng):
  # Needs represented as urgency; values persist independently of daylight.
  deficits={'phys':min(100,self.hunger*1.4+self.fatigue*.3),'safety':100-self.safety,'belong':100-self.belong,'esteem':100-self.esteem,'purpose':100-self.purpose}
  impacts={
  'eat':{'phys':.95},'rest':{'phys':.65,'safety':.08},'farm':{'phys':.28,'esteem':.16,'purpose':.12},'forage':{'phys':.4,'safety':-.1},'build':{'safety':.65,'esteem':.25,'purpose':.18},'socialize':{'belong':.85,'esteem':.1},'help':{'belong':.7,'esteem':.45},'train':{'esteem':.48,'purpose':.75},'explore':{'purpose':.85,'esteem':.2,'safety':-.25},'guard':{'safety':.6,'esteem':.4},'store':{'safety':.55,'phys':.2}}
  feasible=[a for a in ACTIONS if (a!='eat' or w.food>=1) and (a!='build' or w.plants>=1) and (a!='store' or w.food>=2)]
  if not feasible:return 'rest'
  scores={}
  for a in feasible:
   score=sum(deficits[k]*v for k,v in impacts[a].items())+self.bias[a]+self.mem[a]*4+self.skill[a]*4
   if a=='eat' and self.hunger<12:score-=45
   if a=='rest' and self.fatigue<15:score-=25
   if a=='farm':score+=min(20,w.soil/100)*w.daylight*.7
   if a=='help' and len(self.friends)==0:score-=5
   score+=rng.gauss(0,8)
   scores[a]=score
  return max(scores,key=scores.get)
 def do(self,a,w,rng):
  before=(self.hunger,self.fatigue,self.safety,self.belong,self.esteem,self.purpose)
  success=True
  if a=='eat':
   portion=min(w.food,2.5);w.food-=portion;w.soil+=portion;self.hunger=max(0,self.hunger-portion*13);self.energy=min(100,self.energy+portion*5);success=portion>=1
  elif a=='rest':self.fatigue=max(0,self.fatigue-24);self.energy=min(100,self.energy+8)
  elif a=='farm':
   qty=min(w.plants, 1.0+2.2*self.skill[a]);w.plants-=qty;w.food+=qty*.8;w.soil+=qty*.2;w.harvested+=qty;self.esteem=min(100,self.esteem+2);success=qty>1
  elif a=='forage':
   qty=min(w.plants, .5+1.7*self.skill[a]);w.plants-=qty;w.food+=qty*.85;w.soil+=qty*.15;w.harvested+=qty;success=qty>.5
  elif a=='build':
   qty=min(w.plants,1.5);w.plants-=qty;w.shelter+=qty;self.safety=min(100,self.safety+4);self.esteem=min(100,self.esteem+2);success=qty>=1
  elif a=='socialize':
   other=rng.choice([x for x in w.agents if x.i!=self.i]);self.friends.add(other.i);other.friends.add(self.i);self.belong=min(100,self.belong+12);other.belong=min(100,other.belong+5)
  elif a=='help':
   other=rng.choice([x for x in w.agents if x.i!=self.i]);other.hunger=max(0,other.hunger-5);other.safety=min(100,other.safety+5);self.belong=min(100,self.belong+8);self.esteem=min(100,self.esteem+5);other.friends.add(self.i);self.friends.add(other.i)
  elif a=='train':self.purpose=min(100,self.purpose+8);self.esteem=min(100,self.esteem+5)
  elif a=='explore':self.purpose=min(100,self.purpose+11);self.safety=max(0,self.safety-3)
  elif a=='guard':self.safety=min(100,self.safety+9);self.esteem=min(100,self.esteem+4)
  elif a=='store':
   qty=min(w.food,1.5);w.food-=qty;w.stored+=qty;self.safety=min(100,self.safety+5)
  # Each action leaves an episodic memory; connected practice updates trained skill.
  self.count[a]+=1;self.events.append((a,success));self.skill[a]=min(1,self.skill[a]+(.012 if success else .003));self.mem[a]=max(-3,min(3,self.mem[a]*.92+(.1 if success else -.3)))
  self.fatigue=min(100,self.fatigue+ (3 if a not in ('rest','eat') else 0));self.energy=max(0,self.energy-(1.8 if a not in ('rest','eat') else .2))
  return success

def run():
 worlds=[World('Solara',.7),World('Vespara',.35)];rngs={w.name:random.Random(SEED+z*100000) for z,w in enumerate(worlds)}
 # House and Wellspring energy bookkeeping: light is energy transfer, with no fabricated return.
 house=300000.;wellspring=0.;return_flow=0.;light_total=0.;rows=[];events=[]
 for day in range(1,DAYS+1):
  # Wellspring and return inflows, sunlight output proportional to total inflow with minimum.
  well=75.;incoming_return=return_flow;wellspring+=well;house+=well+incoming_return
  light=min(house,60+.4*(well+incoming_return));house-=light;light_total+=light
  # World sunlight allocations fixed equally; daylight determines absorbed fraction; unabsorbed goes to radiative reservoir.
  return_flow=0.
  for w in worlds:
   rng=rngs[w.name];incident=light/2;absorbed=incident*w.daylight;w.sun_received+=absorbed
   # Sunlight increases plant chemical-energy capacity only if material and water available; abstract resource stock growth.
   # Material moves from soil to plants. Energy ledger tracks absorbed sunlight separately, not as newly created mass.
   growth=min(w.soil,absorbed*.30, max(0,650-w.plants));w.soil-=growth;w.plants+=growth
   # Detrital turnover: shelter weathering returns material to soil.
   decay=w.shelter*.003;w.shelter-=decay;w.soil+=decay
   # Stored food released if stockpile is low; all transfers preserve mass.
   if w.food<20 and w.stored>0:
    q=min(3,w.stored);w.stored-=q;w.food+=q
   # Food spoilage moves food to soil, not vanishing.
   spoiled=w.food*.006;w.food-=spoiled;w.soil+=spoiled
   # Ecological food-web abstraction not yet animal agent population; this test focuses on creations.
   rng.shuffle(w.agents)
   for ag in w.agents:
    ag.hunger=min(100,ag.hunger+4.4);ag.fatigue=min(100,ag.fatigue+2.2)
    ag.safety=max(0,min(100,ag.safety-.7+min(1,w.shelter/100)*.3))
    ag.belong=max(0,ag.belong-.75);ag.esteem=max(0,ag.esteem-.5);ag.purpose=max(0,ag.purpose-.6)
    a=ag.choose(w,rng);ok=ag.do(a,w,rng);w.decisions[a]+=1
    if ag.hunger>85:ag.health=max(0,ag.health-1.4)
    elif ag.hunger<30:ag.health=min(100,ag.health+.25)
    if ag.fatigue>85:ag.health=max(0,ag.health-.3)
    events.append({'world':w.name,'day':day,'actor':ag.i,'action':a,'success':int(ok),'hunger':round(ag.hunger,2),'safety':round(ag.safety,2),'belong':round(ag.belong,2),'esteem':round(ag.esteem,2),'purpose':round(ag.purpose,2),'skill':round(ag.skill[a],3)})
   # Energy radiated to world environment is retained in world-energy reservoir; illustrative 3-way toll on food metabolic transitions.
   # Energy flows back after one day via Underworld proxy; toll debit from sunlight-absorbed reservoir only.
   toll=min(w.sun_received, sum(1 for a in w.agents if a.count['eat']>0)*.08)
   w.sun_received-=toll;return_flow+=toll*.7;w.toll+=toll
   # 30% toll retained in world/Underworld reservoirs, included in world energy ledger conceptually.
   w.sun_received+=toll*.3
   material=w.plants+w.soil+w.food+w.shelter+w.stored
   rows.append({'day':day,'world':w.name,'plants':round(w.plants,4),'soil':round(w.soil,4),'food':round(w.food,4),'shelter':round(w.shelter,4),'stored':round(w.stored,4),'material_total':round(material,6),'avg_hunger':round(statistics.mean(a.hunger for a in w.agents),3),'avg_safety':round(statistics.mean(a.safety for a in w.agents),3),'avg_belong':round(statistics.mean(a.belong for a in w.agents),3),'avg_esteem':round(statistics.mean(a.esteem for a in w.agents),3),'avg_purpose':round(statistics.mean(a.purpose for a in w.agents),3),'avg_health':round(statistics.mean(a.health for a in w.agents),3),'avg_friends':round(statistics.mean(len(a.friends) for a in w.agents),3),'house':round(house,4)})
 summaries=[]
 for w in worlds:
  rr=[r for r in rows if r['world']==w.name];summaries.append({'world':w.name,'daylight':w.daylight,'initial_material':1620.,'final_material':rr[-1]['material_total'],'final':rr[-1],'actions':dict(w.decisions),'mean_training_skill':round(statistics.mean(a.skill['train'] for a in w.agents),3),'mean_unique_actions':round(statistics.mean(len(a.count) for a in w.agents),2),'total_events':sum(len(a.events) for a in w.agents),'harvested':round(w.harvested,2)})
 for filename,data in [('founders_v011_turns.csv',rows),('founders_v011_actor_events.csv',events)]:
  with open('/mnt/data/'+filename,'w',newline='') as f:
   wr=csv.DictWriter(f,fieldnames=data[0].keys());wr.writeheader();wr.writerows(data)
 result={'seed':SEED,'days':DAYS,'actors_per_world':N,'summary':summaries,'house_final':house,'wellspring_total':wellspring,'sunlight_emitted':light_total,'limitations':['Plant growth mass transfers soil to plants; no element-level stoichiometry','Sunlight energy bookkeeping is illustrative and not a complete coupled energy audit','No predator/herbivore individual agents in this social-focused experiment','No reproduction, deaths, Founder decision autonomy or explicit ten-layer Underworld','Motivational choices are heuristic with episodic reinforcement, not sophisticated planning']}
 with open('/mnt/data/founders_v011_results.json','w') as f:json.dump(result,f,indent=2)
 print(json.dumps(result,indent=2))
if __name__=='__main__':run()
