"""States, Kingdoms, Nations, Realms; practice and validated vows.

No free Nodes, no routine overload, no conflation of Soul Realm with geographic realm.
All thresholds below are scenario parameters, not fictional canon numbers.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

class AbilityOutcome(str,Enum):
    SUCCESS='success'
    REJECTED='safe_rejection'
    OVERLOAD='exceptional_overload'

@dataclass
class Vow:
    id:str
    terms:str
    validated:bool=False
    breached:bool=False

@dataclass
class State:
    id:str
    nodes:frozenset[str]
    evidence:frozenset[str]
    schema_depth:float
    vow_id:str|None=None

@dataclass
class SoulNetwork:
    actor_id:str
    intrinsic_mode:int=0
    ascendant_nodes:set[str]=field(default_factory=set)
    descendant_nodes:set[str]=field(default_factory=set)
    practiced_nodes:dict[str,set[str]]=field(default_factory=dict)
    vows:dict[str,Vow]=field(default_factory=dict)
    states:dict[str,State]=field(default_factory=dict)
    kingdoms:dict[str,frozenset[str]]=field(default_factory=dict)
    nations:dict[str,frozenset[str]]=field(default_factory=dict)
    realms:dict[str,frozenset[str]]=field(default_factory=dict)
    emperor_node:bool=False
    events:list[dict]=field(default_factory=list)

    def __post_init__(self):
        if self.intrinsic_mode not in range(12):raise ValueError('Temple mode must be one of 12')

    def practice(self,node:str,experience_id:str):
        if not experience_id or not node:raise ValueError('practice must identify an event and node')
        self.practiced_nodes.setdefault(node,set()).add(experience_id)
        self.events.append(dict(event='practice',node=node,experience=experience_id))

    def make_vow(self,vow_id,terms):
        if vow_id in self.vows or not terms:raise ValueError('invalid new vow')
        self.vows[vow_id]=Vow(vow_id,terms)

    def validate_vow(self,vow_id,validated_by):
        if not validated_by:raise ValueError('validation must have evidence/source')
        v=self.vows[vow_id]
        if v.breached:raise ValueError('a breached vow needs a new contract')
        v.validated=True
        self.events.append(dict(event='vow_validation',vow=vow_id,source=validated_by))

    def breach_vow(self,vow_id,action_event):
        if not action_event:raise ValueError('breach requires explicit action event')
        v=self.vows[vow_id];v.breached=True
        self.events.append(dict(event='vow_breach',vow=vow_id,source=action_event))

    def develop_state(self,state_id,nodes,schema_depth,minimum_experiences=2,vow_id=None):
        nodes=frozenset(nodes)
        if state_id in self.states or not nodes:raise ValueError('invalid State')
        if schema_depth<=0:raise ValueError('schema depth required')
        if vow_id is not None:
            v=self.vows[vow_id]
            if not v.validated or v.breached:raise ValueError('unvalidated or breached vow')
        evidence=set()
        for node in nodes:
            ev=self.practiced_nodes.get(node,set())
            if len(ev)<minimum_experiences:raise ValueError('insufficient practice')
            evidence.update(ev)
        s=State(state_id,nodes,frozenset(evidence),schema_depth,vow_id)
        self.states[state_id]=s
        self.events.append(dict(event='state_developed',state=state_id,evidence=sorted(evidence)))

    def _check_state(self,ids):
        ids=frozenset(ids)
        if len(ids)<1 or not ids.issubset(self.states):raise ValueError('unknown State')
        for i in ids:
            s=self.states[i]
            if s.vow_id is not None:
                v=self.vows[s.vow_id]
                if not v.validated or v.breached:raise ValueError('State blocked by vow breach')
        return ids

    def kingdom(self,name,states,compatibility_edges):
        ids=self._check_state(states)
        if name in self.kingdoms or len(ids)<3:raise ValueError('Kingdom needs 3 distinct States')
        # Compatibility must connect all states, not merely the first two.
        adj={x:set() for x in ids}
        for a,b in compatibility_edges:
            if a in ids and b in ids:adj[a].add(b);adj[b].add(a)
        seen=set();stack=[next(iter(ids))]
        while stack:
            a=stack.pop()
            if a not in seen:seen.add(a);stack+=list(adj[a]-seen)
        if seen!=set(ids):raise ValueError('Kingdom states are not compatible/connected')
        self.kingdoms[name]=ids

    def nation(self,name,states):
        ids=self._check_state(states)
        if name in self.nations or len(ids)<4:raise ValueError('Nation needs 4 distinct States')
        self.nations[name]=ids

    def earn_emperor(self,experience_ids,minimum=4,validated_vow=None):
        known=set().union(*self.practiced_nodes.values()) if self.practiced_nodes else set()
        if len(set(experience_ids)&known)<minimum:raise ValueError('insufficient practiced schema evidence')
        if validated_vow is not None:
            v=self.vows[validated_vow]
            if not v.validated or v.breached:raise ValueError('invalid spiritual validation')
        self.emperor_node=True

    def realm(self,name,kingdom_names):
        ids=frozenset(kingdom_names)
        if name in self.realms or len(ids)<4 or not self.emperor_node or not ids.issubset(self.kingdoms):
            raise ValueError('Realm needs 4 Kingdoms and Emperor Node')
        self.realms[name]=ids

    def activate(self,state_id,manipulated_energy,supplied_energy,control_capacity,ledger=None,source=None):
        self._check_state([state_id]);
        if any(x<0 for x in (manipulated_energy,supplied_energy,control_capacity)):
            raise ValueError('negative energy or control')
        # Exceptional mismatch criterion is a test parameter; not a universal law.
        exceptional=(manipulated_energy>5*max(supplied_energy,1e-9)
                     and manipulated_energy>3*max(control_capacity,1e-9))
        if manipulated_energy>supplied_energy or manipulated_energy>control_capacity:
            return AbilityOutcome.OVERLOAD if exceptional else AbilityOutcome.REJECTED
        if supplied_energy>0:
            if ledger is None or not source or ledger.energy[source]+1e-9<supplied_energy:
                return AbilityOutcome.REJECTED
            ledger.move(energy=[(source,'environment:work_heat',supplied_energy)])
        return AbilityOutcome.SUCCESS
