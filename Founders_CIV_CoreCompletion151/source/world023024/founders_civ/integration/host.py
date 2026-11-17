"""Trusted, opt-in hooks around the actual WORLD-024 CommonsWorld.

Extensions get immutable observational DTOs, never a direct mutable Book.
The host alone advances simulation and performs vetted native interventions.
Third-party Python extensions execute local code: load ONLY trusted modules.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from types import MappingProxyType
from collections import Counter
from typing import Any
import hashlib, json
from .contracts import API_VERSION, ScenarioSpec, CompatibilityError

@dataclass(frozen=True)
class EventEnvelope:
    event_key: str
    origin: str
    cycle: int
    action: str
    actor: str | None
    transaction_id: int | None
    parent_event_id: str | None
    payload_json: str  # serialized original event; no invention of missing data

@dataclass(frozen=True)
class Observation:
    cycle: int
    founders: int
    shared_tree_state: str
    shared_tree_population: int
    active_private_trees: int
    stewards: int
    harvest_mass: float
    energy_from_tree: float
    conserved_mass_error: float
    conserved_energy_error: float

class Extension:
    api_version = API_VERSION
    id = 'unnamed'
    requires = ()

    def on_start(self, observation: Observation): pass
    def on_event(self, event: EventEnvelope): pass
    def on_cycle(self, observation: Observation): pass
    def on_finish(self, observation: Observation): pass
    def report(self): return {}

class EventTally(Extension):
    id='event_tally'
    def __init__(self): self.counts=Counter()
    def on_event(self, event): self.counts[f'{event.origin}:{event.action}']+=1
    def report(self): return {'counts':dict(sorted(self.counts.items()))}

class TreeWatch(Extension):
    id='tree_watch'
    def __init__(self):self.timeline=[];self.last_state=None;self.transitions=[]
    def on_cycle(self,o):
        if o.shared_tree_state!=self.last_state:
            self.transitions.append({'cycle':o.cycle,'state':o.shared_tree_state})
        self.last_state=o.shared_tree_state
        self.timeline.append({'cycle':o.cycle,'population':o.shared_tree_population,
            'stewards':o.stewards,'harvest_mass':o.harvest_mass,'state':o.shared_tree_state})
    def report(self): return {'state_transitions':self.transitions,'sampled_timeline':self.timeline[::10]+(self.timeline[-1:] if self.timeline and len(self.timeline)%10!=1 else [])}

BUILTIN_EXTENSIONS={'event_tally':EventTally, 'tree_watch':TreeWatch}

class IntegrationHost:
    """Reuses the real bootstrap and CommonsWorld. No toy engine."""
    def __init__(self, spec: ScenarioSpec, extensions: tuple[Extension,...]|None=None):
        from founders_civ.experimental.world024 import CommonsWorld
        from run_world_tree_pilot import bootstrap
        self.spec=spec
        if extensions is None:
            extensions=tuple(BUILTIN_EXTENSIONS[name]() for name in spec.extensions)
        self.extensions=tuple(extensions)
        names=[x.id for x in self.extensions]
        if len(names)!=len(set(names)):raise CompatibilityError('duplicate extension ID')
        for ext in self.extensions:
            if ext.api_version!=API_VERSION:raise CompatibilityError(f'{ext.id}: incompatible plugin API {ext.api_version}')
            missing=set(ext.requires)-set(names)
            if missing:raise CompatibilityError(f'{ext.id}: missing dependencies {sorted(missing)}')
        def factory(**kw):
            return CommonsWorld(**kw,governance=spec.governance,extraction=spec.extraction,
                   allow_private=spec.allow_private,social_mode=spec.social_mode)
        self.sim,self.realm_id,self.tree_id=bootstrap(seed=spec.seed,simulator_class=factory)
        self.sim.mark_shared(self.tree_id)
        for shock in spec.stress:self.sim.set_stress(**asdict(shock))
        self._cursors={'founder':len(self.sim.events),'ecology':len(self.sim.ecology.events)}
        self._seen_keys=set()
        self._started=False
        self._steps=0
        self._audit_initial=self.sim.book.audit()

    def _observation(self):
        s=self.sim.summary_024();audit=s['conservation']
        return Observation(s['ticks'],s['founders'],s['shared_tree_state'],s['shared_tree_population'],
            s['private_worlds_active'],s['enlisted'],s['harvested_mass'],s['energy_from_tree'],
            audit['mass_error'],audit['energy_error'])

    def _events(self):
        # Preserve source IDs and exactly-once delivery, even if worlds collapse.
        sources={'founder':self.sim.events,'ecology':self.sim.ecology.events}
        out=[]
        for origin,events in sources.items():
            cursor=self._cursors[origin]
            for i in range(cursor,len(events)):
                e=events[i]
                rawid=str(e.get('event_id',f'{origin}:index:{i}'))
                eid=f'{origin}:{rawid}'
                if eid in self._seen_keys:raise AssertionError(f'duplicate event identity {eid}')
                self._seen_keys.add(eid)
                cycle=int(e.get('tick',e.get('day',self.sim.tick)))
                out.append(EventEnvelope(eid,origin,cycle,str(e.get('action','unknown')),
                  e.get('actor'),e.get('transaction_id'),e.get('parent_event_id'),
                  json.dumps(e,sort_keys=True,default=str)))
            self._cursors[origin]=len(events)
        # Deterministic cross-source ordering, no false claim of wall-clock simultaneity.
        return sorted(out,key=lambda x:(x.cycle,x.origin,x.event_key))

    def step(self):
        if self._steps>=self.spec.cycles:raise ValueError('configured compatibility-run horizon exceeded')
        if not self._started:
            self._started=True
            o=self._observation()
            for ext in self.extensions:ext.on_start(o)
        self.sim.step()
        self._steps+=1
        for event in self._events():
            for ext in self.extensions:ext.on_event(event)
        o=self._observation()
        if o.founders!=100:raise AssertionError('founder count drift')
        if self.sim.ecology.day!=self.sim.tick:raise AssertionError('clock drift')
        for ext in self.extensions:ext.on_cycle(o)
        return o

    def run(self):
        for _ in range(self.spec.cycles):self.step()
        if not self._started:
            self._started=True
            for ext in self.extensions:ext.on_start(self._observation())
        last=self._observation()
        for ext in self.extensions:ext.on_finish(last)
        return {'adapter_version':API_VERSION,'branch':'WORLD-024','scenario':self.spec.to_dict(),
             'initial_audit':self._audit_initial,'final_observation':asdict(last),
             'summary':self.sim.summary_024(), 'extensions':{ext.id:ext.report() for ext in self.extensions},
             'events_forwarded':len(self._seen_keys),
             'scenario_digest':hashlib.sha256(json.dumps(self.spec.to_dict(),sort_keys=True).encode()).hexdigest()}

    def export_snapshot(self):
        """JSON-safe, read-only export; NOT a loadable continuation checkpoint."""
        return {'schema':'founders.integration.snapshot/1.0','observation':asdict(self._observation()),
                'branches':['CORE-018','SOCIAL-021','WORLD-022','WORLD-023','WORLD-024'],
                'caveat':'read-only; not a simulation resume snapshot'}
