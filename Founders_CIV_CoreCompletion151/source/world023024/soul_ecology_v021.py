"""Founders-CIV v0.20 adapter: Soul-network ecology A/B tests.

This module deliberately imports the existing v0.20 Population and Book without
altering its reproduction, age cutoff, material-state transformations, or
energy costs. Scenario-only habitat hazard is held constant across arms.
Tunable values here are experimental, not canon.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import defaultdict
from random import Random
from statistics import mean
from typing import Optional
import hashlib, json

from founders_civ.experimental.evolution import Population


def stable_random(seed:int, *parts) -> float:
    payload='|'.join(map(str,(seed,)+parts)).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], 'big')/2**64


def limit(x:float)->float: return max(0.,min(1.,x))

@dataclass
class Episode:
    id: str
    day: int
    context: str
    destination: str
    kind: str  # instruction, observation, practice, result
    source: Optional[str]
    value: float
    encoding_strength: float
    salient: bool
    recalls: int = 0

@dataclass
class RouteBelief:
    destination:str
    context:str
    quality:float   # hypothesis: higher = safer
    confidence:float
    source:Optional[str]
    last_day:int
    support:list[str]=field(default_factory=list)

@dataclass
class RouteCognition:
    actor_id:str
    episodes:list[Episode]=field(default_factory=list)
    beliefs:dict[tuple[str,str],RouteBelief]=field(default_factory=dict)
    route_skill:dict[str,float]=field(default_factory=dict)
    source_trust:dict[str,float]=field(default_factory=dict)
    failures:int=0
    observed_templates:int=0
    practiced:int=0
    retrieved:int=0
    revisions:int=0

    def episode(self, day,context,destination,kind,source,value,salient=False):
        ev=Episode(f'{self.actor_id}:{len(self.episodes)+1}',day,context,destination,kind,
                   source,limit(value),.85 if salient else .65,salient)
        self.episodes.append(ev)
        return ev

    def instruct(self,day,context,destination,source,quality=.85):
        # Observation does not produce trained proficiency or route eligibility.
        event=self.episode(day,context,destination,'instruction',source,quality)
        k=(context,destination)
        tr=self.source_trust.get(source,.65)
        new=limit(.25+.45*tr)
        if k not in self.beliefs:
            self.beliefs[k]=RouteBelief(destination,context,quality,new,source,day,[event.id])
        else:
            b=self.beliefs[k]
            b.quality=limit(.75*b.quality+.25*quality)
            b.confidence=limit(b.confidence+.08*tr)
            b.last_day=day;b.support.append(event.id)
        self.observed_templates+=1

    def retrieve(self,day,context,destination,decay=.13):
        b=self.beliefs.get((context,destination))
        if not b:return 0.0
        # Cue-dependent accessibility. Knowledge is retained, not deleted.
        age=max(0,day-b.last_day)
        repetitions=sum(1 for e in self.episodes if e.context==context and e.destination==destination)
        activation=b.confidence*(1+0.11*min(repetitions,5)) / (1+decay*age)
        if activation>=.25:
            self.retrieved+=1
            return limit(activation)
        return 0.

    def practice(self,day,context,destination,safe,source=None):
        event=self.episode(day,context,destination,'practice',source,1. if safe else 0.,salient=not safe)
        self.practiced+=1
        old=self.route_skill.get(destination,0.)
        # Prediction error and direct practice improve procedural skill.
        self.route_skill[destination]=limit(old+(.19 if safe else .07)*(1-old))
        k=(context,destination)
        if k not in self.beliefs:
            self.beliefs[k]=RouteBelief(destination,context,.55,.55,None,day,[event.id])
        else:
            b=self.beliefs[k]
            expectation=b.quality
            b.quality=limit(expectation+.48*((1. if safe else 0.)-expectation))
            b.confidence=limit(b.confidence+(.14 if safe else -.08))
            b.last_day=day;b.support.append(event.id)
            if abs(b.quality-expectation)>.15:self.revisions+=1
            if b.source:
                self.source_trust[b.source]=limit(self.source_trust.get(b.source,.65)+(.05 if safe else -.13))
        if not safe:self.failures+=1
        return event


def stage_for(day,season_length=6):return 'cold' if ((day-1)//season_length)%2==0 else 'mild'
def safe_patch(context):return 'south' if context=='cold' else 'north'

class EcologyTrial:
    def __init__(self,seed,mode='full',n=30,season_length=6,hazard=True,memory_decay=.13):
        if mode not in ('baseline','episodic','social','full'):
            raise ValueError('bad arm')
        if memory_decay < 0:raise ValueError('memory_decay must be nonnegative')
        self.seed=seed;self.mode=mode;self.season_length=season_length;self.hazard=hazard
        self.memory_decay=memory_decay
        self.pop=Population(seed=seed,n=n,food_per_patch=240.)
        # Teaching decisions cannot alter the demographic RNG stream through extra
        # random draws. Preserve the original v0.20 teach() behavior with an
        # independent contact-specific random stream.
        base_teach=self.pop.teach
        def isolated_teach(teacher_id,learner_id,route):
            previous=self.pop.rng
            self.pop.rng=Random(int(stable_random(seed,self.pop.generation,
                                                teacher_id,learner_id,route,'v020-teach')*2**53))
            try:return base_teach(teacher_id,learner_id,route)
            finally:self.pop.rng=previous
        self.pop.teach=isolated_teach
        self.brains={x.id:RouteCognition(x.id) for x in self.pop.people.values()}
        self.metrics=defaultdict(int);self.history=[]
        self._elders=[]
        for patch,context,dest in [('north','cold','south'),('south','mild','north')]:
            elder=next(x for x in self.pop.people.values() if x.patch==patch)
            elder.age=2 # One experienced adult in each starting patch, ALL ARMS identical.
            elder.learned_routes.add('route:'+dest)
            self.brains[elder.id].instruct(0,context,dest,'prior_experience',.9)
            self.brains[elder.id].route_skill[dest]=.55
            self._elders.append((elder.id,context,dest))

    def _social(self,day,context):
        if self.mode not in ('social','full'):
            # Baseline receives original v0.20 teacher mechanism at a matched cadence.
            if self.mode=='baseline' and day%3==0:
                for elder,_,dest in self._elders:
                    teacher=self.pop.people[elder]
                    if not teacher.alive:continue
                    pupils=[x for x in self.pop.people.values() if x.alive and x.patch==teacher.patch and x.id!=elder]
                    for pupil in pupils[:4]:
                        if self.pop.teach(elder,pupil.id,'route:'+dest):self.metrics['heard']+=1
            return
        # Contact based and source tagged. Teaching doesn't grant procedural skill.
        for elder,ctx,dest in self._elders:
            teacher=self.pop.people[elder]
            if not teacher.alive:continue
            pupils=sorted((x for x in self.pop.people.values() if x.alive and x.patch==teacher.patch and x.id!=elder),key=lambda x:x.id)
            for pupil in pupils[:5]:
                # Teacher competence/source quality and contact determine uptake.
                if stable_random(self.seed,day,elder,pupil.id,'teach') < .64:
                    self.brains.setdefault(pupil.id,RouteCognition(pupil.id)).instruct(day,ctx,dest,elder)
                    self.metrics['heard']+=1

    def _choose_moves(self,day,context):
        if self.mode=='baseline':return
        # One opportunity to act per actor. Source knowledge may drive a hypothesis;
        # local risk cue can trigger self-directed exploration even without knowledge.
        for o in sorted(list(self.pop.people.values()),key=lambda x:x.id):
            if not o.alive:continue
            # Only the *other reachable habitat* is known here. The actor is
            # not given safe_patch(context), which belongs to objective world state.
            alternate='south' if o.patch=='north' else 'north'
            brain=self.brains.setdefault(o.id,RouteCognition(o.id))
            # Imperfect local danger perception; draws independent of ecology RNG.
            noise=(stable_random(self.seed,day,o.id,'sense')-.5)*.055
            perceived_danger=((.17 if o.patch!=safe_patch(context) else .018)+noise) if self.hazard else .018+noise
            if perceived_danger<.095:continue
            memory=brain.retrieve(day,context,alternate,decay=self.memory_decay)
            # Familiar evidence increases willingness to migrate; no mandatory move.
            if self.mode=='episodic':
                chance=.025+.29*memory
            elif self.mode=='social':
                chance=.025+.37*memory
            else:
                # Fear is an appraisal of controllability, not a flat skill bonus.
                practice=brain.route_skill.get(alternate,0.)
                chance=.025+.34*memory+.06*practice
            if stable_random(self.seed,day,o.id,'decide')<min(.70,chance):
                # Migration is the existing v0.20 material/energy-consistent action.
                if self.pop.migrate(o.id,alternate):
                    self.metrics['migration']+=1
                    ev=brain.practice(day,context,alternate,safe=(alternate==safe_patch(context)))
                    o.soul.practice('migration',ev.id)
                    if brain.route_skill[alternate]>=.18:
                        # Trained route flag is not granted for hearing instructions.
                        o.learned_routes.add('route:'+alternate)
                    self.metrics['successful_migrations']+=1
            elif self.mode=='full' and stable_random(self.seed,day,o.id,'explore')<.055:
                # Self-discovery is possible even without an existing teacher.
                if self.pop.migrate(o.id,alternate):
                    self.metrics['migration']+=1;self.metrics['exploration']+=1
                    ev=brain.practice(day,context,alternate,safe=(alternate==safe_patch(context)))
                    o.soul.practice('migration',ev.id)
                    if brain.route_skill[alternate]>=.18:o.learned_routes.add('route:'+alternate)

    def _hazard(self,day,context):
        if not self.hazard:return
        sp=safe_patch(context)
        for o in sorted(list(self.pop.people.values()),key=lambda x:x.id):
            if not o.alive:continue
            p=.018 if o.patch==sp else .17
            self.metrics['unsafe_exposures']+=int(o.patch!=sp)
            self.metrics['safe_exposures']+=int(o.patch==sp)
            if stable_random(self.seed,day,o.id,'hazard')<p:
                self.pop.die(o.id,'habitat_event')
                self.metrics['hazard_deaths']+=1
                brain=self.brains.get(o.id)
                if brain:brain.episode(day,context,o.patch,'result',None,0.,salient=True)

    def step(self,day):
        context=stage_for(day,self.season_length)
        self._social(day,context)
        self._choose_moves(day,context)
        previous=set(self.pop.people)
        # Original v0.20 behavior, reproduction and bookkeeping UNMODIFIED.
        self.pop.step(context)
        for id in set(self.pop.people)-previous:
            self.brains[id]=RouteCognition(id)
        self._hazard(day,context)
        active=[x for x in self.pop.people.values() if x.alive]
        self.pop.book.audit()
        row={'day':day,'seed':self.seed,'arm':self.mode,'context':context,'alive':len(active),
             'born':sum(e['event']=='birth' for e in self.pop.events),
             'dead':sum(e['event']=='death' for e in self.pop.events),
             'knowledge':sum(bool(x.learned_routes) for x in active),
             'unsafe':self.metrics['unsafe_exposures'],'hazard_deaths':self.metrics['hazard_deaths'],
             'migration':self.metrics['migration']}
        self.history.append(row)
        return row

    def run(self,steps):
        for day in range(1,steps+1):self.step(day)
        active=[x for x in self.pop.people.values() if x.alive]
        b=list(self.brains.values())
        return dict(seed=self.seed,arm=self.mode,steps=steps,alive=len(active),
             births=sum(e['event']=='birth' for e in self.pop.events),
             deaths=sum(e['event']=='death' for e in self.pop.events),
             hazard_deaths=self.metrics['hazard_deaths'],
             migrations=self.metrics['migration'],
             safe_exposures=self.metrics['safe_exposures'],
             unsafe_exposures=self.metrics['unsafe_exposures'],
             heard=self.metrics['heard'],
             practiced=sum(x.practiced for x in b),
             templates=sum(x.observed_templates for x in b),
             retrieved=sum(x.retrieved for x in b),
             revisions=sum(x.revisions for x in b),
             route_carriers=sum(bool(x.learned_routes) for x in active),
             food_remaining=sum(self.pop.book.mass['food:'+p] for p in self.pop.patches),
             mean_practice_skill=mean([v for x in b for v in x.route_skill.values()]) if any(x.route_skill for x in b) else 0.,
             audit=self.pop.book.audit(),
             history=self.history)
