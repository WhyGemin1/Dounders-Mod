"""Founders-CIV v0.8: reproducible 48-turn illustrative energy ecology.
All parameters invented. Energy stocks only (material mass separately inventoried)."""
import csv,json,random,collections
from pathlib import Path
R=random.Random(42); P=Path('/mnt/data')
W={}
for name,daylight,seed in [('Aster',0.65,1),('Umbra',0.30,2)]:
 W[name]=dict(daylight=daylight,solar=0.,plant=120.,herb=70.,pred=28.,scav=14.,detritus=35.,soil=80.,water=60.,heat=0.,population=10,food=30.,wood=40.,stone=80.,living_trees=20,felled_trees=0,harvests=0,hunts=0,death_events=0)
house=5000.;under=[0.]*10; house_income=0.;solar_total=0.;tolls=0.; actions=[];logs=[]
actors=[dict(id='F-A',kind='Founder',world='Aster',energy=100.,goal='ecology',skill=2,mem=0,inventory={'axe':1}),dict(id='F-U',kind='Founder',world='Umbra',energy=100.,goal='control',skill=2,mem=0,inventory={'axe':1}),dict(id='C-A1',kind='Creation',world='Aster',energy=28.,goal='survive',skill=1,mem=0,inventory={'knife':1}),dict(id='C-A2',kind='Creation',world='Aster',energy=30.,goal='build',skill=1,mem=0,inventory={'axe':1}),dict(id='S-A',kind='Castor',world='Aster',energy=35.,goal='learn',skill=3,mem=0,inventory={'journal':1}),dict(id='C-U1',kind='Creation',world='Umbra',energy=27.,goal='survive',skill=1,mem=0,inventory={'knife':1}),dict(id='C-U2',kind='Creation',world='Umbra',energy=30.,goal='build',skill=1,mem=0,inventory={'axe':1}),dict(id='S-U',kind='Archer',world='Umbra',energy=35.,goal='protect',skill=3,mem=0,inventory={'bow':1})]
# Every state-change toll debits the *energy source* and credits 70% House via Underworld, 20% local world, 10% Underworld holding.
# Here all toll initially enters layer 0; 20% immediately local, 80% enters underworld; of that 70/80 eventually House.
# For simplicity Underworld forwards 70% of collected toll toward House, and 10% is long-term retained in layer 0.
# This is implemented with transit buckets and explicit ledgers.
retained=0.; transit=[0.]*10

def transfer(source,target,amount):
 global house
 if amount<=0:return 0.
 def get(k):
  if k=='house':return house
  world,account=k.split(':');return W[world][account]
 def change(k,d):
  global house
  if k=='house':house+=d
  else:
   world,account=k.split(':');W[world][account]+=d
 amount=min(amount,max(0.,get(source)));change(source,-amount);change(target,amount);return amount

def transform_toll(world,source,amount):
 global retained,tolls
 # charged on energy used in explicit state-changing actions; taken from source energy account
 if amount<=0:return 0.
 paid=min(amount,W[world][source]);W[world][source]-=paid
 W[world]['soil']+=.2*paid;retained+=.1*paid;transit[0]+=.7*paid;tolls+=paid
 return paid

# Energy accounting: actor energy is separate, so include actor pool in audit.
def total():return house+retained+sum(transit)+sum(sum(w[k] for k in ('solar','plant','herb','pred','scav','detritus','soil','water','heat')) for w in W.values())+sum(a['energy'] for a in actors)
# food represents material inventory and is not additionally energy-counted: harvest takes plant energy to actors through consumption directly.
# initialize energy baseline
initial=total()

def move(w,src,dst,amount):
 amount=min(max(0.,amount),max(0.,w[src]));w[src]-=amount;w[dst]+=amount;return amount

def metabolic(a,w,need):
 # Actor work/maintenance dissipates energy into world heat; no material-state toll for mere expenditure
 spend=min(a['energy'],need);a['energy']-=spend;w['heat']+=spend

def eat(a,w,amount):
 # consume plant energy through food material; 10% state-change toll from plant source
 consumed=min(amount,w['plant'],w['food']*2)
 if consumed<=0:return 0
 w['food']-=consumed/2; w['plant']-=consumed
 a['energy']+=.8*consumed;w['heat']+=.1*consumed
 # toll split from 10% input, explicit source already debited
 global retained,tolls
 w['soil']+=.02*consumed;retained+=.01*consumed;transit[0]+=.07*consumed;tolls+=.1*consumed
 return consumed

def event(a,t,decision,reason,delta=0):
 a['mem']+=1
 if decision in ('research','farm','protect','build','chop') and a['mem']%4==0:a['skill']+=1
 actions.append(dict(turn=t,world=a['world'],actor=a['id'],kind=a['kind'],goal=a['goal'],action=decision,reason=reason,energy=round(a['energy'],2),skill=a['skill'],memory_events=a['mem']))

for t in range(1,49):
 # transfer delayed toll through ten Underworld layers, 2.5 EU/layer/turn
 out=min(2.5,transit[-1]);transit[-1]-=out;house+=out;house_income+=out
 for i in range(8,-1,-1):
  amt=min(2.5,transit[i]);transit[i]-=amt;transit[i+1]+=amt
 # Founder-adjusted daylength: F-U changes Umbra on turn 25
 if t==25:W['Umbra']['daylight']=.55
 for name,w in W.items():
  # House irradiates each world, sun power depends on daylight; nighttime included as mean per turn
  sun=min(house,20*w['daylight']);house-=sun;w['solar']+=sun;solar_total+=sun
  # environmental absorption sunlight to plant/water/soil; sunlight stored, not conjured
  move(w,'solar','plant',sun*.55);move(w,'solar','water',sun*.2);move(w,'solar','soil',sun*.15)
  # remaining solar becomes dissipated environmental heat
  move(w,'solar','heat',sun*.1)
  # photosynthesis: explicit state change toll on 4% plant production energy (plant -> detritus not double charged)
  transform_toll(name,'plant',sun*.55*.04)
  # herbivory transfers plant energy to herbivore biomass, with detritus and toll
  eaten=min(w['plant']*.055,w['herb']*.14+2)
  w['plant']-=eaten;w['herb']+=eaten*.72;w['detritus']+=eaten*.15;w['heat']+=eaten*.03
  w['soil']+=eaten*.02;retained+=eaten*.01;transit[0]+=eaten*.07;tolls+=eaten*.1
  # predation and scavenging
  hunted=min(w['herb']*.06,w['pred']*.12+1)
  w['herb']-=hunted;w['pred']+=hunted*.66;w['detritus']+=hunted*.21;w['heat']+=hunted*.03
  w['soil']+=hunted*.02;retained+=hunted*.01;transit[0]+=hunted*.07;tolls+=hunted*.1
  scavenged=min(w['detritus']*.10,w['scav']*.18+1)
  w['detritus']-=scavenged;w['scav']+=scavenged*.65;w['soil']+=scavenged*.22;w['heat']+=scavenged*.03
  w['soil']+=scavenged*.02;retained+=scavenged*.01;transit[0]+=scavenged*.07;tolls+=scavenged*.1
  # mortality/decay converts animal energy into detritus, heat, and toll
  for key,rate in [('herb',.022),('pred',.035),('scav',.032)]:
   dying=w[key]*rate;w[key]-=dying;w['detritus']+=dying*.8;w['heat']+=dying*.1
   w['soil']+=dying*.02;retained+=dying*.01;transit[0]+=dying*.07;tolls+=dying*.1
  # decomposers return detritus to soil with toll
  decay=min(w['detritus']*.06,5.);w['detritus']-=decay;w['soil']+=decay*.82;w['heat']+=decay*.08
  w['soil']+=decay*.02;retained+=decay*.01;transit[0]+=decay*.07;tolls+=decay*.1
 # actor decision phase, rule-based independent choices
 for a in actors:
  w=W[a['world']]
  metabolic(a,w,1.1 if a['kind']=='Founder' else 1.8)
  # sunlight replenishes actors: allocate world water stored energy as proxy to avoid energy creation
  uptake=min(w['water'],.5*w['daylight']);w['water']-=uptake;a['energy']+=uptake
  if a['energy']<18 and a['kind']!='Founder':
   amt=eat(a,w,8.);event(a,t,'eat','low internal reserve')
  elif a['kind']=='Founder':
   if a['id']=='F-U' and t==25:
    event(a,t,'change_daylight','resource security and control')
   elif w['plant']<90:
    event(a,t,'restore','ecological resilience')
    # shift stored soil energy into plant, paying toll
    amt=move(w,'soil','plant',4);transform_toll(a['world'],'plant',amt*.1)
   else:event(a,t,'observe','monitor energy ecology')
  elif a['kind']=='Castor':
   if a['energy']>=12:
    metabolic(a,w,1.);event(a,t,'research','preserve and develop knowledge')
   else:event(a,t,'rest','insufficient reserve')
  elif a['kind']=='Archer':
   if w['pred']>26:
    metabolic(a,w,.7);event(a,t,'protect','predator pressure')
   else:event(a,t,'patrol','routine security')
  elif a['goal']=='build':
   if w['wood']<20 and w['living_trees']>0 and a['energy']>12:
    w['living_trees']-=1;w['felled_trees']+=1;w['wood']+=5
    # tree->felled tree changes state; energy from actor; toll accounted via actor reserve
    paid=min(a['energy'],1.);a['energy']-=paid;w['heat']+=paid*.9;w['soil']+=paid*.02;retained+=paid*.01;transit[0]+=paid*.07;tolls+=paid*.1
    event(a,t,'chop','wood shortage; living tree to felled tree')
   elif w['wood']>=1 and a['energy']>10:
    w['wood']-=1;w['stone']-=min(.2,w['stone']);metabolic(a,w,.6);event(a,t,'build','shelter improvement')
   else:event(a,t,'rest','materials or energy constrained')
  else:
   if w['food']<22 and w['plant']>5 and a['energy']>10:
    w['food']+=4;w['harvests']+=1;metabolic(a,w,.8);event(a,t,'farm','food reserve below target')
   elif w['pred']>32 and a['energy']>12:
    event(a,t,'avoid','high predator pressure')
   else:event(a,t,'forage','maintain reserves')
 logs.append(dict(turn=t,house=round(house,5),underworld_transit=round(sum(transit),5),underworld_retained=round(retained,5),solar_emitted_cumulative=round(solar_total,5),house_received_cumulative=round(house_income,5),tolls_cumulative=round(tolls,5),energy_total=round(total(),6),energy_error=round(total()-initial,8),**{f'{n}_{k}':round(w[k],4) if isinstance(w[k],float) else w[k] for n,w in W.items() for k in ('daylight','plant','herb','pred','scav','detritus','soil','water','heat','food','wood')}))

assert max(abs(r['energy_error']) for r in logs)<1e-5,max(abs(r['energy_error']) for r in logs)
for path,rows in [(P/'founders_v08_turns.csv',logs),(P/'founders_v08_decisions.csv',actions)]:
 with path.open('w',newline='') as f:
  wr=csv.DictWriter(f,fieldnames=rows[0].keys());wr.writeheader();wr.writerows(rows)
summary=dict(initial_energy=initial,final_energy=total(),max_energy_error=max(abs(r['energy_error']) for r in logs),sunlight_sent=solar_total,house_returned=house_income,universal_tolls=tolls,underworld_transit=sum(transit),underworld_retained=retained,worlds={n:{k:round(v,3) if isinstance(v,float) else v for k,v in w.items()} for n,w in W.items()},decisions=dict(collections.Counter(a['action'] for a in actions)),actors=actors,parameters='Invented: 48 hourly turns; 2 worlds; 8 named actors; 10 Underworld layers; toll 10% of selected state-change energy, 70% transit to House, 20% local soil, 10% Underworld retained; sunlight 20 EU * daylight fraction per world/turn; toy ecological transfer rates.')
(P/'founders_v08_summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k not in ('actors','worlds')},indent=2));print('Worlds:',{n:{k:round(w[k],1) for k in ('plant','herb','pred','scav','food','wood')} for n,w in W.items()})
