"""Ledger-funded experimental inheritance, demographic turnover, migration and culture.

Every feed, birth, and death changes existing material accounts and pays a
transformation toll. Actor reserves are authoritative ledger accounts; genes and
learned route memories are separate, with no genetic inheritance of learned skills.
The population dynamics are deliberately abstract; rates are NOT canon biology.
"""
from __future__ import annotations
from dataclasses import dataclass,field
from random import Random
from statistics import mean
from ..core.ledger import Book
from .soul import SoulNetwork

@dataclass
class Organism:
    id:str
    species:str
    genotype:dict[str,float]
    patch:str
    parents:tuple[str,str]|None=None
    age:int=0
    learned_routes:set[str]=field(default_factory=set)
    alive:bool=True
    soul:SoulNetwork|None=None

class Population:
    def __init__(self,seed:int=17,n:int=30,food_per_patch:float=250.,mutation_sd:float=.045):
        if n<4 or food_per_patch<0 or mutation_sd<0:raise ValueError('invalid population parameters')
        self.rng=Random(seed);self.book=Book();self.people={};self.generation=0
        self.mutation_sd=mutation_sd;self.events=[];self.next_id=0
        self.patches=('north','south')
        for p in self.patches:
            self.book.seed_mass(f'food:{p}',food_per_patch)
            self.book.seed_energy(f'food_energy:{p}',food_per_patch*3.75)
        self.book.seed_energy('ecology_work',20000.)
        self.book.seed_energy('house',100.)
        for i in range(n):
            p=self.patches[i%2];a=self._new_id()
            self.people[a]=Organism(a,'grazer',{'cold_tolerance':self.rng.random(),'foraging_efficiency':self.rng.random()},p,soul=SoulNetwork(a))
            self.book.seed_mass(f'live:{a}',1.)
            self.book.seed_energy(f'animal:{a}',5.)
        self.book.freeze()

    def _new_id(self):
        self.next_id+=1
        return f'G{self.next_id:05}'

    def energy(self,id):return self.book.energy[f'animal:{id}']

    def _transform(self,src,dst,quantity=1.,additional_energy=()):
        w=.25*quantity
        return self.book.transform([(src,dst,quantity)],source='ecology_work',work=w,
                   energy_outputs=[('ecology_work','environment:heat',w*.9),*additional_energy])

    def teach(self,teacher_id,learner_id,route):
        teacher=self.people[teacher_id];learner=self.people[learner_id]
        if not teacher.alive or not learner.alive or route not in teacher.learned_routes:return False
        if teacher.patch!=learner.patch:return False
        if self.rng.random()<.72:
            learner.learned_routes.add(route)
            eventid=f'learning:{len(self.events)}:{teacher_id}:{learner_id}'
            learner.soul.practice('migration',eventid)
            self.events.append(dict(event='learned_route',id=eventid,source=teacher_id,learner=learner_id,route=route))
            return True
        return False

    def reproduce(self,mother_id,father_id):
        mother=self.people[mother_id];father=self.people[father_id]
        if mother.id==father.id or not mother.alive or not father.alive or mother.patch!=father.patch:
            return None
        if min(mother.age,father.age)<1 or min(self.energy(mother.id),self.energy(father.id))<2:
            return None
        src=f'food:{mother.patch}'
        if self.book.mass[src]<1:return None
        newborn=self._new_id()
        traits={}
        for trait in mother.genotype:
            inherited=(mother.genotype[trait]+father.genotype[trait])/2
            traits[trait]=max(0,min(1,inherited+self.rng.gauss(0,self.mutation_sd)))
        self._transform(src,f'live:{newborn}',additional_energy=[
            (f'animal:{mother.id}',f'animal:{newborn}',.4),
            (f'animal:{father.id}',f'animal:{newborn}',.4)])
        child=Organism(newborn,mother.species,traits,mother.patch,parents=(mother.id,father.id),soul=SoulNetwork(newborn))
        # Knowledge explicitly starts empty; teaching is a separate social event.
        self.people[newborn]=child
        self.events.append(dict(event='birth',id=newborn,parents=child.parents,genotype=traits))
        return newborn

    def die(self,organism_id,reason):
        o=self.people[organism_id]
        if not o.alive:return False
        e=self.energy(o.id)
        self._transform(f'live:{o.id}',f'dead:{o.patch}',
            additional_energy=[(f'animal:{o.id}','environment:heat',e)] if e>0 else [])
        o.alive=False
        self.events.append(dict(event='death',id=o.id,reason=reason))
        return True

    def migrate(self,organism_id,destination):
        o=self.people[organism_id]
        if not o.alive or destination not in self.patches or o.patch==destination:return False
        self._move_live(o,destination)
        return True

    def _move_live(self,o,destination):
        # Geographic movement changes actor position, not biomass material state.
        e=self.energy(o.id);cost=min(e,.12)
        if cost>0:self.book.move(energy=[(f'animal:{o.id}','environment:heat',cost)])
        o.patch=destination
        self.events.append(dict(event='migration',id=o.id,destination=destination))

    def step(self,climate='cold'):
        if climate not in ('cold','mild'):raise ValueError('unknown climate')
        self.generation+=1
        population=[o for o in self.people.values() if o.alive]
        self.rng.shuffle(population)
        for o in population:
            if not o.alive:continue
            o.age+=1
            e=self.energy(o.id)
            # Metabolic heat transfer is not a material-state transformation.
            if e>0:self.book.move(energy=[(f'animal:{o.id}','environment:heat',min(e,.18))])
            food=f'food:{o.patch}';food_e=f'food_energy:{o.patch}'
            if self.book.mass[food]>=.08 and self.book.energy[food_e]>=.3:
                self._transform(food,f'dead:waste:{o.patch}',.08,
                                additional_energy=[(food_e,f'animal:{o.id}',.3)])
            fitness=(o.genotype['cold_tolerance'] if climate=='cold'
                     else 1-o.genotype['cold_tolerance']*.35)
            if o.age>9 or self.energy(o.id)<=.05 or self.rng.random()<.17*(1-fitness):
                self.die(o.id,'age_or_environment');continue
            alternative=self.patches[1-self.patches.index(o.patch)]
            if ('route:'+alternative in o.learned_routes and
                self.book.mass[f'food:{alternative}']>self.book.mass[food]*1.4):
                self._move_live(o,alternative)
        active=[o for o in self.people.values() if o.alive]
        for child in [x for x in active if x.parents and x.age<=2]:
            for parent in child.parents:
                if parent in self.people and self.people[parent].alive:
                    for route in sorted(self.people[parent].learned_routes):
                        self.teach(parent,child.id,route)
        for p in self.patches:
            adults=[o for o in active if o.alive and o.patch==p and o.age>=1 and self.energy(o.id)>=2]
            self.rng.shuffle(adults)
            for j in range(0,len(adults)-1,2):
                a,b=adults[j:j+2]
                if self.rng.random()<.48 and self.book.mass[f'food:{p}']>=1:
                    self.reproduce(a.id,b.id)
        return self.summary()

    def summary(self):
        alive=[x for x in self.people.values() if x.alive]
        return dict(generation=self.generation,alive=len(alive),
                    cold_tolerance_mean=mean([x.genotype['cold_tolerance'] for x in alive]) if alive else None,
                    route_knowledge=sum(bool(x.learned_routes) for x in alive),
                    births=sum(x['event']=='birth' for x in self.events),
                    deaths=sum(x['event']=='death' for x in self.events),
                    mass_audit=self.book.audit())
