"""Founder identity, paired origin, manual House checkpoints and funded rebirth.

Scope: psychological continuity/energy only. No Founder body matter is simulated;
therefore these operations are not a claim to model physical death transformations.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from copy import deepcopy
from random import Random
from .soul import SoulNetwork

@dataclass
class Checkpoint:
    version: int
    skills: dict[str,float]
    memories: list[str]
    schemas: dict[str,float]
    goals: list[str]
    soul_snapshot: SoulNetwork

@dataclass
class Founder:
    id: str
    partner_id: str
    location: str = 'house'
    alive: bool = True
    skills: dict[str,float] = field(default_factory=dict)
    memories: list[str] = field(default_factory=list)
    schemas: dict[str,float] = field(default_factory=dict)
    goals: list[str] = field(default_factory=list)
    inventory: dict[str,float] = field(default_factory=dict)
    soul: SoulNetwork | None = None
    checkpoint: Checkpoint | None = None
    checkpoint_version: int = 0
    deaths: int = 0

class FounderRegistry:
    def __init__(self,book,seed:int=42,n:int=100,rebirth_cost:float=2.0):
        if n != 100: raise ValueError('canon requires exactly 100 Founders')
        if rebirth_cost < 0: raise ValueError('invalid rebirth cost')
        self.book=book; self.rebirth_cost=rebirth_cost; self.events=[]
        rng=Random(seed); ids=[f'F{i:03}' for i in range(1,n+1)]
        shuffled=ids[:];rng.shuffle(shuffled)
        partners={}
        for j in range(0,len(shuffled),2):
            a,b=shuffled[j:j+2];partners[a]=b;partners[b]=a
        self.people={i:Founder(i,partners[i],soul=SoulNetwork(i)) for i in ids}
        for f in self.people.values(): self._save(f)

    def _save(self,f):
        f.checkpoint_version+=1
        f.checkpoint=Checkpoint(f.checkpoint_version,deepcopy(f.skills),
                                list(f.memories),deepcopy(f.schemas),list(f.goals),deepcopy(f.soul))
        self.events.append(dict(event='checkpoint',founder=f.id,version=f.checkpoint_version))

    def checkpoint(self,founder_id):
        f=self.people[founder_id]
        if not f.alive or f.location!='house':raise ValueError('checkpoints require living Founder at House')
        self._save(f)

    def learn(self,founder_id,skill,progress,memory):
        f=self.people[founder_id]
        if not f.alive:raise ValueError('inactive Founder cannot learn')
        if progress<=0: raise ValueError('progress must be positive')
        f.skills[skill]=f.skills.get(skill,0.0)+progress;f.memories.append(memory)
        self.events.append(dict(event='experience',founder=f.id,skill=skill,memory=memory))

    def die(self,founder_id):
        f=self.people[founder_id]
        if not f.alive: raise ValueError('already inactive')
        acct=f'founder:{f.id}'
        held=self.book.energy[acct]
        # Physical possessions are not rolled back or recreated: their material
        # moves from the owner's account to the site of death.
        material=[(f'goods:{f.id}:{item}',f'goods:dropped:{f.location}:{item}',q)
                  for item,q in f.inventory.items() if q>0]
        legs=[(acct,'environment:released_energy',held)] if held>0 else []
        if material or legs:self.book.move(material=material,energy=legs)
        f.inventory.clear()
        f.alive=False;f.deaths+=1;f.location='liminal'
        self.events.append(dict(event='death',founder=f.id,released_energy=held))
        return self.rebirth(founder_id)

    def rebirth(self,founder_id):
        f=self.people[founder_id]
        if f.alive:raise ValueError('already active')
        if self.book.energy['house']+1e-9<self.rebirth_cost:
            self.events.append(dict(event='rebirth_pending',founder=f.id))
            return False
        if self.rebirth_cost>0:self.book.move(energy=[('house',f'founder:{f.id}',self.rebirth_cost)])
        cp=f.checkpoint
        f.skills=deepcopy(cp.skills);f.memories=list(cp.memories)
        f.schemas=deepcopy(cp.schemas);f.goals=list(cp.goals)
        f.soul=deepcopy(cp.soul_snapshot)
        # Inventory was dropped to the environment at death, not restored.
        f.location='house'; f.alive=True
        self.events.append(dict(event='rebirth',founder=f.id,version=cp.version))
        return True

    def integrity(self):
        return len(self.people)==100 and all(
            f.partner_id!=i and self.people[f.partner_id].partner_id==i
            for i,f in self.people.items())
