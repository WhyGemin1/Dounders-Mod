"""Founders-CIV SOCIAL-021 — inspectable autonomous Founder social-agent pilot.

Uses the *existing* FounderRegistry, Book and RSW-K Cognition/KnowledgeWorld.
This is an executable experimental scheduler, NOT yet wired into core.engine.Simulation.step.

Rules: 100 Founders, 8 historical squads of 12, 4 provisional officers,
50 random reciprocal close pairs. Historical squad/office membership is a
TEST ALLOCATION, not the canonical character roster. Titles never lock skills.
All material/energy movements are applied by Book; information cannot create energy.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import Counter, defaultdict
from copy import deepcopy
from hashlib import blake2b
from math import exp
from random import Random
from typing import Optional

from ..core.ledger import Book
from .founders import FounderRegistry
from knowledge_architecture import Claim, Cognition, KnowledgeWorld, encounter

SITES = ('house', 'riverbank', 'fields', 'ridge')
LINKS = {'house': ('riverbank','fields'), 'riverbank': ('house','ridge'),
         'fields': ('house','ridge'), 'ridge': ('riverbank','fields')}
GOALS = ('mastery','research','exploration','solidarity','leadership','security')
SKILLS = ('craft','research','navigation','teaching','coordination','survival')
CLAIMS = {
    'river_flow': ('riverbank', 'energy_flow'),
    'ridge_route': ('ridge', 'navigation'),
    'field_care': ('fields', 'cultivation'),
    'house_history': ('house', 'social_history'),
}
COST = {'practice':.13,'study':.12,'explore':.085,'move':.055,'aid':.06,
        'teach':.10,'coordinate':.16,'organize':.11,'recruit':.09,
        'checkpoint':.03,'rest':.012,'recharge':0.0,
        'promise':.035,'endorse':.05,'reflect':.025}


def stable_seed(*values):
    return int.from_bytes(blake2b('|'.join(map(str,values)).encode(), digest_size=8).digest(),'big')


@dataclass
class SocialState:
    id: str
    historical_squad: str
    officer: bool
    initial_specialty: str
    ambition: float
    curiosity: float
    empathy: float
    caution: float
    main_goal: str
    secondary_goal: str
    role_identity: str
    cognition: Cognition = field(default_factory=Cognition)
    faction_id: Optional[str] = None
    contacts: Counter = field(default_factory=Counter)
    aspiration: float = 0.0
    last_goal_change: int = 0
    accomplishments_at_change: int = 0
    goal_progress: Counter = field(default_factory=Counter)
    progress_at_change: int = 0
    initial_skill_total: float = 0.0
    accomplishments: int = 0
    saved_cognition: Optional[Cognition] = None
    saved_faction_id: Optional[str] = None
    saved_goal: Optional[str] = None
    known_proposals: set[str] = field(default_factory=set)


@dataclass
class Faction:
    id: str
    founder_id: str
    agenda: str
    formed_tick: int
    members: set[str] = field(default_factory=set)
    join_events: list[str] = field(default_factory=list)


@dataclass
class FactionProposal:
    id: str
    leader: str
    agenda: str
    deadline: int
    supporters: set[str] = field(default_factory=set)


@dataclass
class Promise:
    id: str
    giver: str
    recipient: str
    due_tick: int
    status: str = 'open'


class SocialSimulation:
    def __init__(self, seed=400, social_mode='full', energy_per_founder=2.8, capture=False, host_world=None):
        if social_mode not in ('full','no_partner','no_teach','no_faction','neutral_trust','isolated'):
            raise ValueError('unknown ablation')
        self.seed=seed; self.mode=social_mode; self.tick=0; self.capture=capture
        self.observations=[]
        self.rng=Random(seed)
        self.host_world=host_world
        self.book=host_world.book if host_world is not None else Book()
        if host_world is None:
            self.book.seed_mass('world:marker', 10.)
            self.book.seed_energy('house', 6000.)
            self.book.seed_energy('river_pool', 2400.)
            self.book.seed_energy('environment:heat', 0.)
        else:
            # Transfer existing physical reserves; never seed new energy after freeze.
            self.book.move(energy=[('house','river_pool',2400.)])
        self.founders=FounderRegistry(self.book,seed=seed,n=100,rebirth_cost=2.)
        self.states={}
        self.factions={}
        self.proposals={}
        self.promises={}
        self.events=[];self.snapshots=[];self.counter=Counter();self.next_event=0
        self.knowledge=KnowledgeWorld()
        for k,(loc,subject) in CLAIMS.items():
            self.knowledge.add(Claim(k,subject,f'Knowledge concerning {subject}',kind='procedure'))
        for index,f in enumerate(self.founders.people.values()):
            rg=Random(stable_seed(seed,f.id,'psychology'))
            officer=index>=96
            squad='OFFICERS' if officer else f'SQ{index//12+1:02d}'
            specialty=SKILLS[(index//3+index%5)%len(SKILLS)]
            g=GOALS[index%len(GOALS)]
            alt=GOALS[(index*5+2)%len(GOALS)]
            ambition=rg.uniform(.15,.95)
            ss=SocialState(f.id,squad,officer,specialty,ambition,rg.uniform(.20,.95),
                          rg.uniform(.20,.95),rg.uniform(.18,.9),g,alt,specialty,
                          aspiration=rg.uniform(.30,.8))
            ss.cognition.attention=rg.uniform(.45,.9)
            ss.cognition.metacognition=rg.uniform(.35,.85)
            self.states[f.id]=ss
            for sk in SKILLS:
                f.skills[sk]=rg.uniform(.06,.22)+(0.20 if sk==specialty else 0.)
            f.goals=[g,alt]
            ss.initial_skill_total=sum(f.skills.values())
            # Initialize checkpoint *after* assigning the Founder's starting
            # capabilities; otherwise a first rebirth erases their baseline.
            self.founders._save(f)
            if host_world is None:
                self.book.seed_energy(f'founder:{f.id}',energy_per_founder)
            else:
                self.book.move(energy=[('house',f'founder:{f.id}',energy_per_founder)])
        if host_world is None:self.book.freeze()
        for x in self.states.values():
            x.saved_cognition=deepcopy(x.cognition)
            x.saved_goal=x.main_goal

    def log(self, action, actor, parent=None, txn=None, **details):
        self.next_event+=1
        rec={'event_id':f'SOC-{self.next_event:08d}', 'tick':self.tick,
             'action':action, 'actor':actor, 'parent_event_id':parent,
             'transaction_id':txn.seq if txn else None, **details}
        self.events.append(rec);self.counter[action]+=1
        return rec['event_id']

    def _contact(self, a, b):
        if a==b:return False
        if self.mode=='isolated':return False
        return self.founders.people[a].location==self.founders.people[b].location

    def _trust(self, a,b,dimension='benevolence'):
        if self.mode=='neutral_trust':return .5
        return self.states[a].cognition.partner(b).expectation(dimension)

    def _nearby(self, a, rng):
        site=self.founders.people[a].location
        others=[b for b,p in self.founders.people.items() if b!=a and p.location==site and p.alive]
        if self.mode=='isolated':return []
        rg=self.states[a]
        partner=self.founders.people[a].partner_id
        weighted=[]
        for b in others:
            weight=1.0 + (2.8 if self.states[b].historical_squad==rg.historical_squad else 0.)
            if b==partner and self.mode!='no_partner':weight+=8.5
            weight+=min(2.5, rg.contacts[b]*.12)
            weighted.append((b,weight))
        # Sample no more than four physical encounters per decision, weighted without replacement.
        chosen=[]
        for _ in range(min(4,len(weighted))):
            total=sum(w for _,w in weighted)
            r=rng.random()*total
            for j,(b,w) in enumerate(weighted):
                r-=w
                if r<=0:
                    chosen.append(b);weighted.pop(j);break
        return chosen

    def _energy(self,a):return self.book.energy[f'founder:{a}']

    def _pay(self,a,action,extra=0):
        q=COST[action]+extra
        if q<=0:return None
        # A proposal is not permission to overdraw. Binary-float balances
        # slightly below q must reject gracefully instead of reaching Book.
        if self._energy(a)<q:return False
        return self.book.move(energy=[(f'founder:{a}','environment:heat',q)])

    def _goal_boost(self,s,action):
        g=s.main_goal
        return {
            'mastery':{'practice':1.0,'study':.25},
            'research':{'study':1.1,'teach':.1},
            'exploration':{'explore':1.0,'study':.15},
            'solidarity':{'aid':1.0,'coordinate':.55,'teach':.4,'promise':.4},
            'leadership':{'organize':1.1,'recruit':1.0,'coordinate':.5},
            'security':{'checkpoint':.5,'recharge':.4,'aid':.2},
        }.get(g,{}).get(action,0.)

    def _proposals(self,a,contacts):
        s=self.states[a]; f=self.founders.people[a]; energy=self._energy(a)
        proposals=[]
        def add(action, base, target=None, meta=None):
            if energy+1e-8 < COST[action]:return
            score=base+self._goal_boost(s,action)
            # Ambition increases willingness to attempt high-effort goals, not raw competence.
            if action in ('practice','study','explore','organize','recruit'):
                score+=.55*s.ambition
            if action in ('aid','coordinate','teach','recruit') and target is not None:
                score+=.62*(self._trust(a,target)-.5)
                if target==f.partner_id and self.mode!='no_partner':score+=.55
            proposals.append((score,action,target,meta))
        add('practice',.58+s.ambition*.10)
        add('study',.50+s.curiosity*.55)
        add('explore',.37+s.curiosity*.15)
        add('rest',.02+.30*s.caution)
        if self.tick-s.last_goal_change>=6:
            stagnation=s.goal_progress[s.main_goal]-s.progress_at_change < 2
            add('reflect',.15+.8*(stagnation)+.3*s.curiosity)
        if f.location=='house' and len(f.memories)>=3 and len(f.memories)%4 in (0,1):
            add('checkpoint',.30 + .45*s.caution)
        if energy<1.15 and f.location in ('house','riverbank'):
            add('recharge',2.3+(1.15-energy)*1.4)
        elif energy<1.15 and f.location!='house':
            add('move',2.,meta='house')
        for b in contacts:
            open_commitments=[p for p in self.promises.values() if p.giver==a and p.recipient==b and p.status=='open']
            if open_commitments:
                add('aid',1.8+s.empathy*.4,target=b)
            elif self.tick>1 and s.empathy>.45 and s.contacts[b]>0:
                add('promise',.18+.45*s.empathy,target=b)
            t=self._trust(a,b)
            if energy >= .32 and self._energy(b)<energy+.4:
                add('aid',.23+s.empathy*.65 + .25*t,target=b)
            add('coordinate',.18+s.empathy*.35+.30*t,target=b)
            known=[k for k,v in s.cognition.knowledge.items() if v.understanding>.075]
            if known and self.mode!='no_teach':
                chosen=max(known,key=lambda k:s.cognition.knowledge[k].understanding)
                known_by_target=self.states[b].cognition.knowledge.get(chosen)
                if (known_by_target.exposures if known_by_target else 0)<=s.cognition.knowledge[chosen].exposures:
                    add('teach',.38+.3*s.ambition +.35*t,target=b,meta=chosen)
            if self.mode!='no_faction':
                own_open=next((pr for pr in self.proposals.values() if pr.leader==a),None)
                if s.faction_id is None and self.tick>=3 and s.contacts[b]>=1 and t>.47:
                    if own_open and b not in own_open.supporters and own_open.id not in self.states[b].known_proposals:
                        add('organize',.44+.55*s.ambition,target=b,meta=own_open.id)
                    elif not own_open and self.states[b].main_goal in (s.main_goal,s.secondary_goal):
                        add('organize',.25+.55*s.ambition,target=b)
                if s.faction_id is not None and self.states[b].faction_id is None:
                    add('recruit',.23+.2*s.ambition,target=b)
                elif s.faction_id is None and self.states[b].faction_id is not None:
                    faction=self.factions[self.states[b].faction_id]
                    if faction.agenda==s.main_goal or (t>.68 and faction.agenda==s.secondary_goal):
                        add('recruit',.38+.4*t,target=b,meta='join')
        # Known invitations allow specific meetings, independent of the random
        # background contact sample. Joining still requires physical co-location.
        if self.mode!='no_faction' and s.faction_id is None:
            for pid in sorted(s.known_proposals):
                pr=self.proposals.get(pid)
                if pr and pr.leader!=a and a not in pr.supporters and self._contact(a,pr.leader) and pr.agenda in (s.main_goal,s.secondary_goal):
                    add('endorse',2.30+.8*self._trust(a,pr.leader),target=pr.leader,meta=pid)
        return proposals

    def _choose(self,a,proposals,rng):
        if not proposals:return (0.,'rest',None,None)
        # Gumbel max creates a stochastic but reproducible bounded-rational choice.
        # All proposals and their scores are emitted, making the policy auditable.
        temp=.47
        return max(proposals,key=lambda p:p[0]-temp*__import__('math').log(-__import__('math').log(max(1.e-12,min(1-1.e-12,rng.random())))))

    def _move(self,a,rng,force=None):
        f=self.founders.people[a]
        options=LINKS[f.location]
        # One local graph edge per movement. No teleportation.
        nxt=force if force in options else rng.choice(options)
        txn=self._pay(a,'explore')
        if txn is False:return ('insufficient_energy',None,{'destination':nxt})
        f.location=nxt
        return ('moved',txn,{'destination':nxt})

    @staticmethod
    def _goal_progress(s, action, success=True):
        mapping={'practice':'mastery','study':'research','explore':'exploration',
                 'aid':'solidarity','coordinate':'solidarity','teach':'solidarity',
                 'faction_founded':'leadership','faction_join':'leadership',
                 'checkpoint':'security','recharge':'security'}
        if success and action in mapping:
            s.goal_progress[mapping[action]] += 1

    def _do(self,a,choice,contacts,rng,parent):
        _,act,target,meta=choice
        s=self.states[a];f=self.founders.people[a]
        if act=='recharge':
            source='house' if f.location=='house' else ('river_pool' if f.location=='riverbank' else None)
            if source is None:return self.log('failed',a,parent,reason='not_at_energy_source')
            q=min(1.15,self.book.energy[source])
            if q<=0:return self.log('failed',a,parent,reason='energy_source_empty')
            txn=self.book.move(energy=[(source,f'founder:{a}',q)])
            self._goal_progress(s,'recharge')
            return self.log('recharge',a,parent,txn,amount=q,source=source)
        if act=='explore' or act=='move':
            outcome,txn,details=self._move(a,rng,force=meta)
            if txn is not None:
                s.accomplishments+=1
                self._goal_progress(s,'explore')
            return self.log('explore' if act=='explore' else 'move',a,parent,txn,outcome=outcome,**details)
        if act in ('aid','coordinate','teach','recruit','organize','promise','endorse') and (target is None or not self._contact(a,target)):
            return self.log('failed',a,parent,reason='recipient_unavailable',target=target)
        txn=self._pay(a,act)
        if txn is False:return self.log('failed',a,parent,reason='insufficient_energy',attempted=act)
        if act=='rest':
            return self.log('rest',a,parent,txn)
        if act=='reflect':
            before=s.main_goal
            # Reflection may reorganize goals after insufficient progress. It
            # neither improves technical competence nor guarantees success.
            slow=s.goal_progress[s.main_goal]-s.progress_at_change<2
            if slow and rng.random()<.35+.40*s.curiosity:
                s.main_goal=s.secondary_goal if s.secondary_goal!=s.main_goal else rng.choice([g for g in GOALS if g!=before])
                f.goals=[s.main_goal, before]
                s.secondary_goal=before
            s.last_goal_change=self.tick
            s.accomplishments_at_change=s.accomplishments
            s.progress_at_change=s.goal_progress[s.main_goal]
            return self.log('reflect',a,parent,txn,goal_before=before,goal_after=s.main_goal,stagnated=slow)
        if act=='checkpoint':
            if f.location!='house':return self.log('failed',a,parent,reason='checkpoint_requires_house')
            self.founders.checkpoint(a)
            self._goal_progress(s,'checkpoint')
            s.saved_cognition=deepcopy(s.cognition)
            s.saved_faction_id=s.faction_id
            s.saved_goal=s.main_goal
            return self.log('checkpoint',a,parent,txn,checkpoint_version=f.checkpoint_version)
        if act=='practice':
            domain=s.initial_specialty if s.main_goal=='mastery' else rng.choice(SKILLS)
            current=f.skills.get(domain,0.)
            # Real action and energy cost; diminishing returns toward a mechanical soft ceiling.
            # Keep skills within their defined 0..1 representation. A saturated
            # skill cannot gain more practice progress or emit invalid updates.
            delta=min(max(.002,(1-current)*(.024+.032*s.ambition)*rng.uniform(.75,1.15)),
                      max(0.,1.-current))
            if delta>0:
                self.founders.learn(a,domain,delta,f'practice:{self.tick}:{domain}')
            s.accomplishments+=1
            self._goal_progress(s,'practice')
            return self.log('practice',a,parent,txn,skill=domain,gain=round(delta,6),new_skill=round(f.skills[domain],6))
        if act=='study':
            local=[k for k,(site,subject) in CLAIMS.items() if site==f.location]
            if not local:
                return self.log('study',a,parent,txn,outcome='no_local_sources')
            claim=rng.choice(local)
            before=s.cognition.claim(claim).understanding
            eid=encounter(self.knowledge,s.cognition,self.tick,a,claim,source='local_observation',
                          medium='observation',fidelity=rng.uniform(.45,.90),trust=.5)
            f.schemas[claim]=s.cognition.claim(claim).understanding
            s.accomplishments+=1
            self._goal_progress(s,'study')
            return self.log('study',a,parent,txn,claim=claim,knowledge_event=eid,
                            comprehension_gain=round(s.cognition.claim(claim).understanding-before,6))
        if act=='aid':
            # Helping a second Founder transfers ACTUAL budgeted energy; no phantom gain.
            amt=min(.11,max(0.,self._energy(a)-.15))
            t2=self.book.move(energy=[(f'founder:{a}',f'founder:{target}',amt)]) if amt else None
            if self.mode!='neutral_trust':
                self.states[target].cognition.partner(a).update('benevolence',True,strength=.5)
            fulfilled=[]
            if amt>=.08:
                for p in self.promises.values():
                    if p.giver==a and p.recipient==target and p.status=='open':
                        p.status='fulfilled';fulfilled.append(p.id)
                        if self.mode!='neutral_trust':
                            self.states[target].cognition.partner(a).update('integrity',True,strength=1.0)
            s.contacts[target]+=1;self.states[target].contacts[a]+=1
            s.accomplishments+=1
            self._goal_progress(s,'aid')
            return self.log('aid',a,parent,t2 or txn,target=target,amount=amt,fulfilled_promises=fulfilled,effort_txn=txn.seq if txn else None)
        if act=='coordinate':
            tf=self.founders.people[target]
            # Physical feasibility and practiced coordination matter, not trust by itself.
            competence=(f.skills.get('coordination',0)+tf.skills.get('coordination',0))/2
            success=rng.random()<(.25+.55*competence)
            if success:
                # Learned coordination is bounded; at full skill the attempt
                # can still succeed without adding a negative skill increment.
                for who,rate,partner in ((a,.010,target),(target,.008,a)):
                    cur=self.founders.people[who].skills['coordination']
                    increment=max(0.,min(rate*(1.-cur),1.-cur))
                    if increment>0:
                        self.founders.learn(who,'coordination',increment,
                                            f'joint:{self.tick}:{partner}')
                s.accomplishments+=1
                self._goal_progress(s,'coordinate')
            if self.mode!='neutral_trust':
                self.states[target].cognition.partner(a).update('ability',success,strength=.4)
                s.cognition.partner(target).update('ability',success,strength=.35)
            s.contacts[target]+=1;self.states[target].contacts[a]+=1
            return self.log('coordinate',a,parent,txn,target=target,success=success,
                            skill_mean=round(competence,5))
        if act=='teach':
            claim=meta
            if claim not in s.cognition.knowledge or s.cognition.claim(claim).understanding<=.075:
                return self.log('failed',a,parent,reason='no_teachable_knowledge')
            r=self.states[target];t=self._trust(target,a,'ability')
            fidelity=min(.96,.40+.4*f.skills.get('teaching',.1)+.25*s.cognition.claim(claim).understanding)
            before=r.cognition.claim(claim).understanding
            keid=encounter(self.knowledge,r.cognition,self.tick,target,claim,source=a,
                           medium='spoken',fidelity=fidelity,trust=t)
            s.contacts[target]+=1;r.contacts[a]+=1;s.accomplishments+=1
            self._goal_progress(s,'teach')
            return self.log('teach',a,parent,txn,target=target,claim=claim,
                            knowledge_event=keid,
                            learner_gain=round(r.cognition.claim(claim).understanding-before,6),
                            fidelity=round(fidelity,4))
        if act=='promise':
            if any(p.giver==a and p.recipient==target and p.status=='open' for p in self.promises.values()):
                return self.log('failed',a,parent,reason='duplicate_promise')
            pid=f'P-{len(self.promises)+1:05d}'
            self.promises[pid]=Promise(pid,a,target,self.tick+3)
            s.contacts[target]+=1;self.states[target].contacts[a]+=1
            return self.log('promise',a,parent,txn,promise=pid,target=target,due_tick=self.tick+3)
        if act=='organize':
            if self.mode=='no_faction' or s.faction_id is not None or self.tick<3:
                return self.log('failed',a,parent,reason='not_eligible_to_organize')
            active=next((pr for pr in self.proposals.values() if pr.leader==a),None)
            if active:
                if target in active.supporters:
                    return self.log('failed',a,parent,reason='already_supporter')
                self.states[target].known_proposals.add(active.id)
                return self.log('faction_invitation',a,parent,txn,proposal=active.id,agenda=active.agenda,target=target)
            # A Founder can propose a faction, but a coalition does not exist until
            # two additional Founders explicitly endorse the agenda.
            pid=f'PR-{self.next_event+1:06d}'
            pr=FactionProposal(pid,a,s.main_goal,self.tick+11,{a})
            self.proposals[pid]=pr
            self.states[target].known_proposals.add(pid)
            return self.log('faction_proposed',a,parent,txn,proposal=pid,agenda=pr.agenda,target=target)
        if act=='endorse':
            pid=meta;pr=self.proposals.get(pid)
            if not pr or pr.leader!=target or pid not in self.states[a].known_proposals or a in pr.supporters:
                return self.log('failed',a,parent,reason='endorsement_invalid')
            if pr.agenda not in (s.main_goal,s.secondary_goal):
                return self.log('failed',a,parent,reason='agenda_mismatch')
            pr.supporters.add(a)
            eid=self.log('faction_endorse',a,parent,txn,proposal=pid,target=target)
            if len(pr.supporters)>=3:
                fid=f'ORG-{len(self.factions)+1:03d}'
                org=Faction(fid,pr.leader,pr.agenda,self.tick,set(pr.supporters))
                self.factions[fid]=org
                for member in pr.supporters:
                    self.states[member].faction_id=fid
                    self._goal_progress(self.states[member],'faction_founded')
                del self.proposals[pid]
                self.log('faction_founded',a,eid,faction=fid,agenda=pr.agenda,members=sorted(org.members))
            else:
                # Supporter repeats the invitation through their own close ties
                for b in contacts:
                    if b!=a and b not in pr.supporters and self.states[b].main_goal==pr.agenda:
                        self.states[b].known_proposals.add(pid)
            return eid
        if act=='recruit':
            if self.mode=='no_faction':return self.log('failed',a,parent,reason='factions_disabled')
            if s.faction_id is None and self.states[target].faction_id:
                # Joining is the acting Founder's choice, not unilateral recruitment.
                org=self.factions[self.states[target].faction_id]
                if org.agenda!=s.main_goal and org.agenda!=s.secondary_goal:
                    return self.log('failed',a,parent,reason='agenda_mismatch')
                s.faction_id=org.id;org.members.add(a);s.accomplishments+=1
                self._goal_progress(s,'faction_join')
                eid=self.log('faction_join',a,parent,txn,faction=org.id,inviter=target)
                org.join_events.append(eid);return eid
            if s.faction_id and self.states[target].faction_id is None:
                org=self.factions[s.faction_id]
                # Invitation is not acceptance; target must later choose to join.
                self.states[target].contacts[a]+=1;s.contacts[target]+=1
                return self.log('faction_invitation',a,parent,txn,faction=org.id,target=target)
            return self.log('failed',a,parent,reason='not_eligible_to_recruit')
        raise AssertionError(act)

    def step(self):
        self.tick+=1
        # Expired commitments update *recipients'* interpretations, not objective intent.
        for p in self.promises.values():
            if p.status=='open' and self.tick>p.due_tick:
                p.status='unfulfilled'
                if self.mode!='neutral_trust':self.states[p.recipient].cognition.partner(p.giver).update('integrity',False,strength=.8)
                self.log('promise_expired',p.giver,target=p.recipient,promise=p.id,reason='unfulfilled_not_proven_deceit')
        for pid,pr in list(self.proposals.items()):
            if self.tick>pr.deadline:
                self.log('proposal_expired',pr.leader,proposal=pid,supporters=len(pr.supporters))
                del self.proposals[pid]
        # No world creation or magic energy amplification. River/House have finite stocks.
        order=list(self.founders.people)
        Random(stable_seed(self.seed,self.tick,'order')).shuffle(order)
        for a in order:
            if not self.founders.people[a].alive:continue
            rng=Random(stable_seed(self.seed,self.tick,a,'decision'))
            contacts=self._nearby(a,rng)
            proposals=self._proposals(a,contacts)
            choice=self._choose(a,proposals,rng)
            deid=self.log('decision',a,chosen=choice[1],goal=self.states[a].main_goal,
                          energy=round(self._energy(a),4),location=self.founders.people[a].location,
                          contacts=contacts,
                          top_alternatives=[{'action':p[1], 'target':p[2], 'score':round(p[0],4)}
                                            for p in sorted(proposals,reverse=True)[:4]])
            self._do(a,choice,contacts,rng,deid)
        audit=self.book.audit()
        if self.capture:
            self.observations.append(self.observation())
        if self.tick==1 or self.tick%5==0:
            self.snapshots.append(self.summary(include_events=False))
        return audit

    def run(self,ticks=20):
        for _ in range(ticks):self.step()
        return self.summary()

    def save_checkpoint(self,actor):
        f=self.founders.people[actor]
        self.founders.checkpoint(actor)
        s=self.states[actor]
        s.saved_cognition=deepcopy(s.cognition)
        s.saved_faction_id=s.faction_id
        s.saved_goal=s.main_goal

    def kill_and_rebirth(self,actor):
        f=self.founders.people[actor]
        before=f.location
        ok=self.founders.die(actor)
        if ok:
            ss=self.states[actor]
            ss.cognition=deepcopy(ss.saved_cognition) if ss.saved_cognition is not None else Cognition()
            ss.main_goal=ss.saved_goal or ss.main_goal
            # External faction memberships/others' trust are NOT rolled back. Founder may
            # be unaware of ongoing affiliation; institutional records persist.
            self.log('rebirth_social_restore',actor,restored_from=before)
        return ok

    def observation(self):
        return {
            'tick':self.tick,
            'actors':[{'id':a,'partner':f.partner_id,'squad':self.states[a].historical_squad,
                       'officer':self.states[a].officer, 'ambition':round(self.states[a].ambition,3),
                       'goal':self.states[a].main_goal,'specialty':self.states[a].initial_specialty,
                       'location':f.location,'faction':self.states[a].faction_id,
                       'skills':{k:round(v,3) for k,v in f.skills.items()},
                       'knowledge':{k:round(v.understanding,3) for k,v in self.states[a].cognition.knowledge.items() if v.exposures>0},
                       'partner_trust':round(self._trust(a,f.partner_id),3)}
                      for a,f in self.founders.people.items()],
            'factions':[{'id':org.id,'agenda':org.agenda,'founder':org.founder_id,
                         'members':sorted(org.members)} for org in self.factions.values()],
            'actions':dict(self.counter),
            'energy_error':round(self.book.audit()['energy_error'],10)
        }

    def summary(self, include_events=True):
        f=self.founders.people
        funcs=self.states
        across=sum(1 for a,p in f.items() if a<p.partner_id and funcs[a].historical_squad!=funcs[p.partner_id].historical_squad)
        informed=sum(any(v.exposures>0 for v in s.cognition.knowledge.values()) for s in funcs.values())
        multi_informed=sum(any(v.exposures>=2 for v in s.cognition.knowledge.values()) for s in funcs.values())
        members=sum(bool(s.faction_id) for s in funcs.values())
        cross_factions=sum(len({funcs[a].historical_squad for a in org.members})>=2 for org in self.factions.values())
        pairs=[s.cognition.partner(f[a].partner_id).expectation('benevolence') for a,s in funcs.items()]
        avg_ambition=sum(s.ambition for s in funcs.values())/100
        practiced=sum(sum(v for k,v in f[a].skills.items()) for a in f)/100
        by_ambition=sorted(funcs,key=lambda x:funcs[x].ambition)
        high=sum(funcs[a].accomplishments for a in by_ambition[-25:])/25
        low=sum(funcs[a].accomplishments for a in by_ambition[:25])/25
        high_skill_gain=sum(sum(f[a].skills.values())-funcs[a].initial_skill_total for a in by_ambition[-25:])/25
        low_skill_gain=sum(sum(f[a].skills.values())-funcs[a].initial_skill_total for a in by_ambition[:25])/25
        cross_teach=sum(e['action']=='teach' and funcs[e['actor']].historical_squad!=funcs[e['target']].historical_squad for e in self.events if e['action']=='teach')
        audit=self.book.audit()
        out={'seed':self.seed,'mode':self.mode,'tick':self.tick,'founders':len(f),
             'pairs':50,'cross_squad_pairs':across,'factions':len(self.factions),
             'faction_members':members,'cross_squad_factions':cross_factions,
             'active_proposals':len(self.proposals),
             'promises_fulfilled':sum(p.status=='fulfilled' for p in self.promises.values()),
             'promises_unfulfilled':sum(p.status=='unfulfilled' for p in self.promises.values()),
             'informed':informed,'multi_exposed':multi_informed,
             'mean_partner_benevolence_trust':round(sum(pairs)/100,6),
             'mean_ambition':round(avg_ambition,6),'mean_total_skill':round(practiced,6),
             'high_ambition_accomplishments':round(high,5),
             'low_ambition_accomplishments':round(low,5),
             'high_ambition_skill_gain':round(high_skill_gain,6),
             'low_ambition_skill_gain':round(low_skill_gain,6),
             'cross_squad_teach_events':cross_teach,
             'knowledge_events':len(self.knowledge.events),
             'energy_mass_audit':audit,
             'actions':dict(self.counter)}
        if include_events:
            out['faction_roster']=[{'id':org.id,'agenda':org.agenda,'founder':org.founder_id,
                                   'size':len(org.members),'cross_squad':len({funcs[i].historical_squad for i in org.members})>=2}
                                    for org in self.factions.values()]
        return out
