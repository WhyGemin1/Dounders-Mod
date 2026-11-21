#!/usr/bin/env python3
"""Founders-CIV v0.14 controlled RSW experiment.
Three conditions: needs+memory (A), individual commitments (B), shared spiritual
beliefs and social coordination (C). C_false: counterfactual erroneous doctrine.
All parameters synthetic. Not a claim about human religion or real ecology.
"""
from __future__ import annotations
import argparse, collections, csv, json, math, random, statistics, os
from dataclasses import dataclass, field
from pathlib import Path

ACTIONS=("farm","forage","fetch_water","dig_canal","build_cistern","build_granary",
         "share","connect","reflect","research","guard","rest","council","ritual")
BELIEFS=("water_stewardship","food_reserve","mutual_care","knowledge","ritual_only")
PROJECTS={"water_stewardship":"dig_canal","food_reserve":"build_granary","mutual_care":"share","knowledge":"research","ritual_only":"ritual"}

# Immutable action scoring data: do not allocate 14 equivalent tables per decision.
EFFECTS={
 "farm":(22,2,2,4,0), "forage":(17,0,1,2,1),"fetch_water":(13,6,0,1,0),
 "dig_canal":(5,17,0,8,9),"build_cistern":(4,19,0,6,7),
 "build_granary":(4,16,1,6,7),"share":(3,10,21,9,7),
 "connect":(0,3,23,5,4),"reflect":(0,4,3,2,20),
 "research":(0,5,1,17,24),"guard":(0,18,3,12,4),
 "rest":(9,9,0,1,1),"council":(0,9,18,7,11),"ritual":(0,5,15,7,14)
}
HUNGER_ACTION_BONUS={"farm":13,"forage":11,"share":1}
THIRST_ACTION_BONUS={"fetch_water":21,"build_cistern":4,"dig_canal":2}
CONVICTION_ACTION={"dig_canal":"water_stewardship","build_cistern":"water_stewardship",
 "build_granary":"food_reserve","share":"mutual_care","research":"knowledge","ritual":"ritual_only"}

@dataclass
class Actor:
    id:int
    food:float; water:float; vitality:float; health:float
    hunger:float; thirst:float; safety:float; belonging:float; esteem:float; purpose:float
    empathy:float; caution:float; curiosity:float; trust:float; agency:float; willingness:float
    fear_style:float; values:dict; convictions:dict
    skill:dict=field(default_factory=dict)
    memories:dict=field(default_factory=dict)
    belief:str=""
    belief_strength:float=0.0
    commitment:float=0.0
    age:int=25
    alive:bool=True
    frail_days:int=0
    action_counts:dict=field(default_factory=lambda:collections.Counter())
    last_council:int=-999
    last_ritual:int=-999
    events:int=0

class World:
    def __init__(self, mode, seed, days=180, log=False):
        self.mode=mode; self.seed=seed;self.rng=random.Random(seed)
        self.days=days;self.log=log
        self.actors=[]
        traits=random.Random(seed*977+23)  # shared actor starts across conditions
        for i in range(36):
            empathy=traits.uniform(.2,.95); caution=traits.uniform(.2,.95)
            curiosity=traits.uniform(.2,.95); trust=traits.uniform(.25,.80)
            agency=traits.uniform(.35,.92); willing=traits.uniform(.3,.9)
            style=traits.uniform(-.8,.95)
            values={"water_stewardship":.25*caution+.40*curiosity+traits.random()*.27,
                    "food_reserve":.45*caution+traits.random()*.32,
                    "mutual_care":.60*empathy+.22*trust+traits.random()*.14,
                    "knowledge":.67*curiosity+traits.random()*.2,
                    "ritual_only":.18+traits.random()*.16}
            actor=Actor(i,traits.uniform(4,8),traits.uniform(4,8),traits.uniform(64,88),
                  traits.uniform(78,100),traits.uniform(9,24),traits.uniform(8,21),
                  traits.uniform(45,75),traits.uniform(38,72),traits.uniform(35,75),
                  traits.uniform(30,75),empathy,caution,curiosity,trust,agency,willing,style,
                  values,{b:0.0 for b in BELIEFS},
                  skill={a:traits.uniform(.1,.5) for a in ACTIONS})
            self.actors.append(actor)
        # material/food stock amounts are not a complete elemental ledger
        self.crop=250.;self.wild=230.;self.natural_water=650.; self.soil=520.
        self.communal_food=210.;self.communal_water=75.
        self.canal=0.;self.cistern=0.;self.granary=0.;self.knowledge=0.
        self.food_spoiled=0.;self.cumulative_food=0.;self.water_drawn=0.
        self.rain_received=0.;self.drought_days=0
        self.trust_index=.52; self.disputes=0;self.dissent_events=0
        self.project_progress=collections.Counter();self.norm=None;self.norm_since=None
        self.norm_days=0;self.shared_rituals=0;self.sacred_tradition=False
        self.meetings=0;self.institution_history=[]
        self.days_underfed=0;self.deaths=0;self.collab_work=0.;self.ind_work=0.
        self.action_count=collections.Counter();self.events=[];self.turns=[]
        self.stores_day0=self.crop+self.wild+self.communal_food+sum(a.food for a in self.actors)
        self.daily_weather=[]
        climate=random.Random(seed*37+7)
        for day in range(days):
            drought=(34<=day<110)
            rain=max(0,climate.gauss(6.0,1.3)) if drought else max(0,climate.gauss(35.0,4.3))
            self.daily_weather.append((drought,rain))
        # Commons shared conditional conservation: food in the common store is deducted on consumption.
        self.rare_disaster=0
        if mode=="C_false":
            # Coordinated misleading testimony by three well-connected actors (a deliberate
            # intervention), rather than a world with inherently worse resources.
            for leader in self.actors[:10]:
                leader.belief="ritual_only"; leader.belief_strength=.98
                leader.convictions["ritual_only"]=.93;leader.trust=.98

    def need_states(self,a):
        """Need deficiencies 0..100; hunger/thirst are urgency, other values lack satisfaction."""
        return {"phys":min(100,.60*a.hunger+.40*a.thirst),"safety":100-a.safety,
                "belonging":100-a.belonging,"esteem":100-a.esteem,"purpose":100-a.purpose}

    def belief_from_experience(self,a,day):
        if self.mode=="A":return
        # Individual interpretation arises from experienced scarcity, social concern,
        # and goal values, rather than direct assignment of a global religion.
        fear=(a.hunger+a.thirst)/200
        threat=min(1,(max(0,620-self.crop-self.wild)/620)+(.27 if 34<=day<110 else 0))
        if 34<=day<110: fear=max(fear,.32)
        for belief in BELIEFS[:-1]:
            urgency={"water_stewardship":a.thirst/100,
                     "food_reserve":a.hunger/100,
                     "mutual_care":(100-a.belonging)/120,
                     "knowledge":(100-a.purpose)/140}[belief]
            life_event=max(0,urgency+.43*threat+.13*fear-.18)
            a.convictions[belief]=min(1,max(0,a.convictions[belief]+.021*a.values[belief]*life_event
                                      -.00055*(1-life_event)))
        if self.mode in ("C","C_false") and a.belief:
            a.convictions[a.belief]=min(1,a.convictions[a.belief]+.0016)
        if self.mode=="C_false" and a.id==0:
            a.convictions["ritual_only"]=max(.85,a.convictions["ritual_only"])

    def felt_utility(self,a, action, day, n=None):
        if n is None:n=self.need_states(a)
        # Practical subjective expected benefits of each action. Values are weighted
        # via individual need deficit and personalized memory adjustment.
        weights=(n["phys"]/100,n["safety"]/100,n["belonging"]/100,
                 n["esteem"]/100,n["purpose"]/100)
        val=sum(x*w for x,w in zip(EFFECTS[action],weights))
        # Hunger/thirst drive *different* food vs water strategies.
        val+=(a.hunger/100)*(HUNGER_ACTION_BONUS.get(action,0))
        val+=(a.thirst/100)*(THIRST_ACTION_BONUS.get(action,0))
        if a.food<2:val+=12 if action in ("farm","forage") else 0
        if a.water<1.8:val+=18 if action=="fetch_water" else 0
        # Structural defenses cannot satisfy immediate scarcity.
        if action in ("dig_canal","build_cistern","build_granary","research"):
            val-=3.2
        if action=="rest":val+=(100-a.vitality)*.32
        if action=="share":val+=4*a.empathy if a.food>3 else -8
        if action=="guard":val+=5*a.caution if 34<=day<110 else 0
        if action=="connect":val+=4*a.empathy
        if action=="research":val+=5*a.curiosity
        if action=="council" and (self.mode not in ("C","C_false") or day-a.last_council<8):return -999
        if action=="ritual" and (self.mode not in ("C","C_false") or day-a.last_ritual<9):return -999
        if a.vitality<15 and action not in ("rest","reflect","connect","ritual"):
            val-=15
        if action=="farm" and self.crop<1:val-=20
        if action=="forage" and self.wild<1:val-=20
        if action=="fetch_water" and self.natural_water<1:val-=22
        if action=="share" and a.food<2:val-=18
        # Infrastructure must have finite useful capacity; no infinite canals.
        if action=="dig_canal" and self.canal>=3.0:return -999
        if action=="build_cistern" and self.cistern>=4.0:return -999
        if action=="build_granary" and self.granary>=4.0:return -999
        # Learned expectations remain bounded, so experience affects but doesn't dictate choices.
        val+=6*max(-1,min(1,a.memories.get(action,0)))
        val+=3*a.skill.get(action,0)
        if self.mode!="A":
            fear=max(0,min(1,(a.hunger+a.thirst)/180))
            # Approach-oriented fear can encourage deliberate investment. Avoidance
            # can favor immediate acquisition or safety at the expense of planning.
            if action in ("dig_canal","build_cistern","build_granary"):
                val+=9*fear*a.fear_style*a.willingness +3*a.caution*a.willingness
            if action in ("forage","fetch_water","guard"):
                val+=6*fear*(1-a.fear_style)*.5
            target=CONVICTION_ACTION.get(action)
            if target:
                val+=17*a.convictions[target]*a.willingness
        if self.mode in ("C","C_false"):
            # A mistaken sacred claim that ritual *replaces* physical preparation
            # can diminish the perceived utility of actual protective projects.
            # This is a specific inaccurate belief, not a general penalty for religion.
            if action in ("dig_canal","build_cistern","build_granary"):
                mistaken=max(0,a.belief_strength if a.belief=="ritual_only" else 0)
                if self.norm=="ritual_only": mistaken=max(mistaken,.65*self.trust_index)
                val-=26*mistaken
            if self.norm:
                target=PROJECTS[self.norm]
                if action==target: val+=12*self.trust_index+9*a.convictions.get(self.norm,0)
                # Conformity can be pressure, not merely agreement.
                if action==target and self.norm=="ritual_only":val+=7
            # Discussions are chosen when social and fear needs motivate them.
            if action=="council": val+=13 if (34<=day<110) else 4
            if action=="ritual": val+=(7 if self.norm else -12) + (9 if self.norm=="ritual_only" else 0)
        return val

    def choose_action(self,a,day):
        n=self.need_states(a)
        candidates=[(self.felt_utility(a,act,day,n),act) for act in ACTIONS]
        # Gumbel random utility allows imperfect decisions and distinct personalities.
        return max(candidates,key=lambda x:x[0]+self.rng.gammavariate(1.5,1.8))[1]

    def execute(self,a,act,day):
        before=(a.food,a.water,a.vitality,a.hunger,a.thirst,a.safety,a.belonging,a.esteem,a.purpose)
        effective_skill=min(2,a.skill.get(act,0))
        stochastic=.82+.36*self.rng.random()
        success=True;reward=0.
        if act=="farm":
            harvest=min(self.crop,2.4*(.85+.35*effective_skill)*stochastic)
            self.crop-=harvest;a.food+=harvest
            success=harvest>.8;reward=1.1 if success else -.65
        elif act=="forage":
            harvest=min(self.wild,2.2*(.85+.25*effective_skill)*stochastic)
            self.wild-=harvest;a.food+=harvest
            success=harvest>.7;reward=1 if success else -.6
        elif act=="fetch_water":
            q=min(self.natural_water,3.7*(.82+.25*effective_skill)*stochastic)
            self.natural_water-=q;a.water+=q;self.water_drawn+=q
            success=q>1.0;reward=1 if success else -.6
        elif act in ("dig_canal","build_cistern","build_granary"):
            if a.vitality<13:success=False;reward=-.45
            else:
                # Enabling actual collective pooling is an institutional benefit,
                # not material creation. Same project available without shared religion.
                boost=1+.28*self.trust_index if self.mode in ("C","C_false") and self.norm and PROJECTS[self.norm]==act else 1
                units=(.9+.35*effective_skill)*stochastic*boost
                if act=="dig_canal":self.canal=min(3.0,self.canal+units*.012)
                elif act=="build_cistern":self.cistern=min(4.0,self.cistern+units*.016)
                else:self.granary=min(4.0,self.granary+units*.016)
                if boost>1:self.collab_work+=units
                else:self.ind_work+=units
                reward=.55
        elif act=="share":
            amount=min(1.65,max(0,a.food-1.2))
            a.food-=amount;self.communal_food+=amount
            a.belonging=min(100,a.belonging+2.1);a.esteem=min(100,a.esteem+1.0)
            self.trust_index=min(.98,self.trust_index+.0007*amount)
            success=amount>.25;reward=.6 if success else -.5
        elif act=="connect":
            a.belonging=min(100,a.belonging+4.2);a.safety=min(100,a.safety+1.1)
            self.trust_index=min(.98,self.trust_index+.00023)
            reward=.7
        elif act=="reflect":
            a.purpose=min(100,a.purpose+5.6);a.safety=min(100,a.safety+1.4)
            a.vitality=min(100,a.vitality+1.3)
            reward=.55
        elif act=="research":
            self.knowledge+=.028*(.9+effective_skill)*stochastic
            a.esteem=min(100,a.esteem+1.9);a.purpose=min(100,a.purpose+2.9)
            reward=.65
        elif act=="guard":
            a.safety=min(100,a.safety+2.9);a.esteem=min(100,a.esteem+1.1)
            reward=.6
        elif act=="rest":
            a.vitality=min(100,a.vitality+14);a.safety=min(100,a.safety+1)
            reward=.65
        elif act=="council":
            a.last_council=day
            self.meetings+=1
            others=[x for x in self.actors if x.alive and x.id!=a.id]
            peer=self.rng.choice(others) if others else None
            # Beliefs arise from personal convictions and risk interpretations;
            # credibility and relationship (trust) influence transmission.
            if a.belief and self.rng.random()<.74:
                proposal=a.belief
            else:
                proposal=max(BELIEFS[:-1], key=lambda b:a.values[b]+a.convictions[b]+self.rng.uniform(-.13,.13))
                if self.mode=="C_false" and a.id==0: proposal="ritual_only"
            if not a.belief or self.rng.random()<.17:
                a.belief=proposal;a.belief_strength=max(.15,a.belief_strength)
            if peer:
                confidence=.28+.35*a.trust+.25*a.belief_strength
                if self.rng.random()<confidence*(.55+.38*peer.trust):
                    if peer.belief!=proposal:
                        peer.belief_strength*=.91
                        if peer.belief_strength<.45:
                            peer.belief=proposal;peer.belief_strength=.26
                    else:peer.belief_strength=min(1,peer.belief_strength+.035)
            a.belief_strength=min(1,a.belief_strength+.045)
            a.belonging=min(100,a.belonging+3.4)
            reward=.55
        elif act=="ritual":
            a.last_ritual=day
            if self.norm:
                self.shared_rituals+=1
                a.belonging=min(100,a.belonging+3.0)
                a.purpose=min(100,a.purpose+2.2)
                a.belief_strength=min(1,a.belief_strength+.08)
                reward=.46
            else: reward=-.3
        a.action_counts[act]+=1;self.action_count[act]+=1;a.events+=1
        a.vitality=max(0,a.vitality-(2.0 if act in ("farm","forage","fetch_water","dig_canal","build_cistern","build_granary") else 1))
        # Each action creates an episodic event; skill is gained only by repeated
        # relevant practice, plus memory alignment. Failure can teach too.
        old=a.memories.get(act,0.)
        a.memories[act]=.90*old+.10*reward
        if act not in ("rest","connect","reflect","council","ritual"):
            a.skill[act]=min(2.5,a.skill.get(act,0.)+(.007 if success else .0025))
        if self.log and (act in ("council","ritual","dig_canal","build_granary","build_cistern") or
                         (day in (34,70,109) and a.id<2)):
            self.events.append({"day":day+1,"actor":a.id,"action":act,"mode":self.mode,
                "belief":a.belief,"norm":self.norm,"success":int(success),
                "hunger":round(a.hunger,1),"thirst":round(a.thirst,1),
                "vitality":round(a.vitality,1),"event_no":a.events})

    def update_group_norm(self,day):
        if self.mode not in ("C","C_false"):return
        count=collections.Counter(a.belief for a in self.actors if a.alive and a.belief and a.belief_strength>.2)
        if not count:return
        b, support=count.most_common(1)[0]
        alive=sum(a.alive for a in self.actors)
        if support>=max(8,math.ceil(.37*alive)):
            if b==self.norm:self.norm_days+=1
            else:
                self.norm=b;self.norm_since=day+1;self.norm_days=1
                self.institution_history.append({"day":day+1,"kind":"norm_created","norm":b,"supporters":support})
        # Beliefs may lose support when not enacted or conditions change.
        if self.norm and self.norm_days>=12 and self.shared_rituals>=8 and not self.sacred_tradition:
            self.sacred_tradition=True
            self.institution_history.append({"day":day+1,"kind":"sacralized_tradition","norm":self.norm,"supporters":support})
        if self.norm and support<5:
            self.norm=None;self.norm_days=0

    def update_day(self,day):
        drought,rain=self.daily_weather[day];self.drought_days+=int(drought)
        # House sunlight held fixed across conditions to isolate social mechanisms.
        sunlight=65.
        self.rain_received+=rain
        self.natural_water=min(2000,self.natural_water+rain*(1+.22*self.cistern)+8.0)
        # Natural growth limited by actual water and soil, plus canal efficiency.
        moisture=min(1,self.natural_water/110)
        growth=min(42,(26.0+min(7,self.knowledge*.16))*moisture*(.64+.47*self.canal))
        growth=min(growth,self.soil/.07 if self.soil>0 else 0)
        crop_used=min(self.natural_water,growth*.24)
        self.natural_water-=crop_used;self.soil-=growth*.07
        self.crop=min(900,self.crop+growth)
        self.wild=min(500,self.wild+(15.0 if not drought else 4.5)*moisture)
        # Soil restitution, ordinary ecological recycling (not modeled chemically).
        self.soil=min(600,self.soil+3.4)
        # Spoilage affects all stores and rises with heat. Granary reduces loss.
        spoil=max(0.0015,.006/(1+.55*self.granary))
        lost=self.communal_food*spoil
        self.communal_food-=lost;self.food_spoiled+=lost
        living=[a for a in self.actors if a.alive]
        # Daily consumption and need changes: personal stock first, then communal.
        self.rng.shuffle(living)
        for a in living:
            needfood=1.0
            take=min(a.food,needfood);a.food-=take;needfood-=take
            communal=min(self.communal_food,needfood);self.communal_food-=communal;needfood-=communal
            needwater=.65
            got=min(a.water,needwater);a.water-=got;needwater-=got
            free=min(self.communal_water,needwater);self.communal_water-=free;needwater-=free
            # Hunger/thirst are integrated physiological conditions, not instant death.
            a.hunger=min(100,max(0,a.hunger+(11 if needfood>.15 else -5.5)))
            a.thirst=min(100,max(0,a.thirst+(14 if needwater>.15 else -6.0)))
            if needfood>.15:self.days_underfed+=1
            a.vitality=min(100,max(0,a.vitality-1.2+(3.0 if needfood<.15 and needwater<.15 else 0)))
            a.safety=max(0,a.safety-.24-(.4 if drought else 0))
            a.belonging=max(0,a.belonging-.36)
            a.esteem=max(0,a.esteem-.18)
            a.purpose=max(0,a.purpose-.28)
            damage=max(0,a.hunger-70)*.005+max(0,a.thirst-65)*.010
            a.health=max(0,min(100,a.health-damage+(.08 if a.hunger<30 and a.thirst<30 else 0)))
            if a.health<=0 or (a.thirst>98 and a.hunger>95 and self.rng.random()<.012):
                a.alive=False;self.deaths+=1;continue
            self.belief_from_experience(a,day)
        # Actors get two opportunities daily. Counters and memories persist.
        for slot in range(2):
            order=[a for a in self.actors if a.alive]
            self.rng.shuffle(order)
            for a in order:
                act=self.choose_action(a,day)
                self.execute(a,act,day)
        self.update_group_norm(day)
        pop=sum(a.alive for a in self.actors)
        all_active=[a for a in self.actors if a.alive]
        stocks=self.crop+self.wild+self.communal_food+sum(a.food for a in all_active)
        self.turns.append({"seed":self.seed,"mode":self.mode,"day":day+1,"population":pop,
            "crop":round(self.crop,4),"wild":round(self.wild,4),"soil":round(self.soil,4),
            "natural_water":round(self.natural_water,4),"common_food":round(self.communal_food,4),
            "common_water":round(self.communal_water,4),"canal":round(self.canal,4),
            "cistern":round(self.cistern,4),"granary":round(self.granary,4),
            "knowledge":round(self.knowledge,4),"mean_health":round(statistics.mean(a.health for a in all_active),2) if all_active else 0,
            "mean_hunger":round(statistics.mean(a.hunger for a in all_active),2) if all_active else 100,
            "mean_thirst":round(statistics.mean(a.thirst for a in all_active),2) if all_active else 100,
            "mean_belonging":round(statistics.mean(a.belonging for a in all_active),2) if all_active else 0,
            "mean_purpose":round(statistics.mean(a.purpose for a in all_active),2) if all_active else 0,
            "trust":round(self.trust_index,4),"norm":self.norm or "",
            "tradition":int(self.sacred_tradition),"rituals":self.shared_rituals,
            "drought":int(drought),"rain":round(rain,4),"material_food_stocks":round(stocks,4)})

    def run(self):
        for day in range(self.days):self.update_day(day)
        living=[a for a in self.actors if a.alive]
        summary={"seed":self.seed,"mode":self.mode,"population_final":len(living),
          "deaths":self.deaths,"mean_health":round(statistics.mean(a.health for a in living),3) if living else 0,
          "mean_hunger":round(statistics.mean(a.hunger for a in living),3) if living else 100,
          "mean_thirst":round(statistics.mean(a.thirst for a in living),3) if living else 100,
          "mean_belonging":round(statistics.mean(a.belonging for a in living),3) if living else 0,
          "mean_esteem":round(statistics.mean(a.esteem for a in living),3) if living else 0,
          "mean_purpose":round(statistics.mean(a.purpose for a in living),3) if living else 0,
          "mean_conviction":round(statistics.mean(max(a.convictions.values()) for a in living),3) if living else 0,
          "scarcity_actor_days":self.days_underfed,
          "crop_final":round(self.crop,2),"wild_final":round(self.wild,2),
          "food_common_final":round(self.communal_food,2),"water_final":round(self.natural_water,2),
          "canal":round(self.canal,2),"cistern":round(self.cistern,2),"granary":round(self.granary,2),
          "knowledge":round(self.knowledge,2),"trust":round(self.trust_index,3),
          "norm":self.norm or "", "sacred_tradition":int(self.sacred_tradition),
          "shared_rituals":self.shared_rituals,"meetings":self.meetings,"norm_events":len(self.institution_history),
          "collab_work":round(self.collab_work,2),"ind_work":round(self.ind_work,2),
          "actions_total":sum(self.action_count.values()),
          "action_counts":dict(self.action_count)}
        return summary

def write_csv(path,rows):
    if not rows:return
    with open(path,"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--seeds",type=int,default=24)
    ap.add_argument("--days",type=int,default=180)
    ap.add_argument("--seed-start",type=int,default=1)
    ap.add_argument("--out",default=str(Path(__file__).resolve().parent/"outputs"))
    args=ap.parse_args();out=Path(args.out);out.mkdir(exist_ok=True,parents=True)
    modes=("A","B","C","C_false")
    summaries=[]; turns=[];events=[];institution_events=[]
    for seed in range(args.seed_start,args.seed_start+args.seeds):
        for mode in modes:
            w=World(mode,seed,args.days,log=(seed==1))
            s=w.run();summaries.append(s)
            if seed==1:
                turns.extend(w.turns);events.extend(w.events)
                for e in w.institution_history:institution_events.append({"mode":mode,"seed":seed,**e})
    # same paired seeds, compare conditions for each metric
    bymode={m:[x for x in summaries if x["mode"]==m] for m in modes}
    keys=["population_final","deaths","scarcity_actor_days","mean_health","mean_hunger","mean_thirst",
          "mean_belonging","mean_esteem","mean_purpose","mean_conviction","canal","cistern","granary",
          "trust","knowledge","sacred_tradition","shared_rituals","meetings","collab_work","actions_total"]
    results={"design":{"agents_per_settlement":36,"days":args.days,"matched_random_seeds":args.seeds,
               "variants":{"A":"Five needs + memory; no personal RSW commitment layer",
                           "B":"A plus personal fear interpretation, values, conviction and willingness",
                           "C":"B plus communicated beliefs, potential shared norms, coordinated work and ritual",
                           "C_false":"C plus one deliberately misleading high-credibility ritual-only advocate"},
               "weather":"Same synthetic rainfall for all modes in each seed; drought days 35 through 110",
               "sunlight":"Identical fixed model sunlight in all modes; not a House energy-flow audit",
               "caveat":"Simplified stock model, no physical mass/energy conservation claim; no human behavioral validation"},
             "means":{m:{k:round(statistics.mean(x[k] for x in bymode[m]),3) for k in keys} for m in modes},
             "stddev":{m:{k:round(statistics.stdev(x[k] for x in bymode[m]),3) for k in keys} for m in modes},
             "seed_1":{m:bymode[m][0] for m in modes}}
    for pair in (("B","A"),("C","B"),("C","A"),("C_false","C")):
        diffs={k:[x[k]-y[k] for x,y in zip(bymode[pair[0]],bymode[pair[1]])] for k in keys}
        results.setdefault("paired_differences",{})[f"{pair[0]}_minus_{pair[1]}"]={
            k:{"mean":round(statistics.mean(v),3),"min":round(min(v),3),"max":round(max(v),3)} for k,v in diffs.items()}
    write_csv(out/"founders_v014_replicates.csv",[{k:v for k,v in row.items() if k!="action_counts"} for row in summaries])
    write_csv(out/"founders_v014_daily_seed1.csv",turns)
    write_csv(out/"founders_v014_actor_events_seed1.csv",events)
    write_csv(out/"founders_v014_institutions_seed1.csv",institution_events)
    (out/"founders_v014_summary.json").write_text(json.dumps(results,indent=2))
    print(json.dumps({"means":results["means"],"paired":{k:{m:v[m]["mean"] for m in ("population_final","scarcity_actor_days","canal","granary","sacred_tradition")} for k,v in results["paired_differences"].items()}},indent=2))
if __name__=="__main__":main()
