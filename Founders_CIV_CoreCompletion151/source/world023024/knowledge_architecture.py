"""RSW-K v0.19 experimental cognitive extension; v0.18 Agent compatible.
No claim to simulate consciousness or v0.18 material physics.
"""
from dataclasses import dataclass, field
from collections import defaultdict
import math

@dataclass(frozen=True)
class Claim:
    id: str
    subject: str
    content: str
    kind: str = 'procedure'
    actual_validity: bool = True  # oracle, never accessible directly to actors
    prerequisites: tuple = ()

@dataclass
class Representation:
    claim_id: str
    medium: str
    holder: str
    fidelity: float = 1.0
    origin_event: str = ''

@dataclass
class KnowledgeRelation:
    exposures: int = 0
    recall: float = 0.0
    understanding: float = 0.0
    confidence: float = 0.5
    practiced: int = 0
    provenance: list = field(default_factory=list)

@dataclass
class TrustRelation:
    ability_alpha: float = 2.0
    ability_beta: float = 2.0
    integrity_alpha: float = 2.0
    integrity_beta: float = 2.0
    benevolence_alpha: float = 2.0
    benevolence_beta: float = 2.0
    def expectation(self, domain='integrity'):
        a=getattr(self,domain+'_alpha');b=getattr(self,domain+'_beta')
        return a/(a+b)
    def update(self, domain, success, strength=1.0):
        fieldname=domain+('_alpha' if success else '_beta')
        setattr(self,fieldname,getattr(self,fieldname)+strength)

@dataclass
class Cognition:
    knowledge: dict = field(default_factory=dict)
    trust: dict = field(default_factory=dict)
    attention: float = 0.7
    metacognition: float = 0.65
    def claim(self, claim_id):
        return self.knowledge.setdefault(claim_id,KnowledgeRelation())
    def partner(self, partner_id):
        return self.trust.setdefault(partner_id,TrustRelation())

class KnowledgeWorld:
    def __init__(self):
        self.claims={}
        self.representations=[]
        self.events=[]
        self.next_event=0
    def add(self, claim):
        if claim.id in self.claims: raise ValueError('Duplicate claim')
        self.claims[claim.id]=claim
    def record(self, tick, actor, event_type, claim_id='', **details):
        self.next_event+=1
        row={'event_id':f'EV-{self.next_event:08d}','tick':tick,'actor':actor,'event_type':event_type,'claim_id':claim_id,**details}
        self.events.append(row)
        return row['event_id']
    def externalize(self, tick, actor, claim_id, medium='archive'):
        if claim_id not in self.claims: raise KeyError(claim_id)
        eid=self.record(tick,actor,'externalize',claim_id,medium=medium)
        self.representations.append(Representation(claim_id,medium,actor,origin_event=eid))
        return eid

def encounter(world, cognition, tick, actor, claim_id, source, medium, fidelity=1.0, trust=0.5):
    """Encounter is not equivalent to understanding, belief, or application."""
    k=cognition.claim(claim_id)
    eid=world.record(tick,actor,'encounter',claim_id,source=source,medium=medium,fidelity=round(fidelity,5),trust=round(trust,5))
    k.exposures+=1
    k.recall=min(1.,k.recall+0.23*fidelity*cognition.attention)
    # Interpretation is bounded by cognitive attention and source fidelity.
    k.understanding=min(1.,k.understanding+0.16*fidelity*cognition.attention)
    # Trust changes belief confidence, not oracle truth.
    k.confidence=min(1.,max(0.,k.confidence+0.13*fidelity*(trust-0.45)))
    k.provenance.append(eid)
    return eid

def practice(world,cognition,tick,actor,claim_id,skill,environment_ok=True):
    k=cognition.claim(claim_id)
    # Knowledge helps action, but is not sufficient without feasibility.
    chance=0.12+0.40*k.understanding+0.42*skill
    success=environment_ok and chance>=0.48
    eid=world.record(tick,actor,'practice',claim_id,success=int(success),feasible=int(environment_ok),skill=round(skill,5),understanding=round(k.understanding,5))
    k.practiced+=1
    if success:
        k.understanding=min(1.,k.understanding+0.09)
        k.confidence=min(1.,k.confidence+0.06)
    else:
        k.confidence=max(0.,k.confidence-0.025*cognition.metacognition)
    k.provenance.append(eid)
    return success
