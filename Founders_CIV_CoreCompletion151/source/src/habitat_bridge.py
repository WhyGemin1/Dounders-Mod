"""Experimental five-guild physical vertical slice, NOT v0.21.7 reproduction engine.
Every animal material/energy account is backed by the WORLD-023 Book.
"""
from dataclasses import dataclass
from random import Random
from collections import Counter

BIOMES=('forest','grassland','wetland','ridge')
SPECIES=('field_mouse','meadow_grazer','forest_browser','ridge_hound','carrion_bird')
HOME={'field_mouse':'grassland','meadow_grazer':'grassland','forest_browser':'forest','ridge_hound':'ridge','carrion_bird':'wetland'}
PREY={'ridge_hound':('field_mouse','meadow_grazer')}
@dataclass
class CohortAnimal:
    id:str
    species:str
    habitat:str
    sex:str
    age:int=0
    alive:bool=True
    parent:str|None=None
    energy:float=0.

class HabitatBridge:
    def __init__(self,tree,seed=9711,counts=None):
        self.tree=tree;self.book=tree.book;self.rng=Random(seed+13813)
        self.actors={};self.events=[];self.serial=0;self.day=0;self.stats=Counter();self.parental_investment=False;self.juvenile_energy_conservation=False
        counts=counts or {'field_mouse':8,'meadow_grazer':6,'forest_browser':6,'ridge_hound':4,'carrion_bird':4}
        for species,n in counts.items():
            if species not in SPECIES or n<0:raise ValueError('invalid cohort')
            for _ in range(n):self._new(species,HOME[species],initial=True)
    def _log(self,kind,**fields):
        row={'event_id':f'bridge:{len(self.events)+1}','day':self.day,'event':kind,**fields}
        self.events.append(row);self.stats[kind]+=1
    def _convert(self,legs):
        work=.0001
        return self.book.transform(legs,source=self.tree.acct('sun','forest'),work=work,energy_outputs=[(self.tree.acct('sun','forest'),'environment:heat',.9*work)])
    def _new(self,species,habitat,initial=False,parent=None):
        self.serial+=1;id=f'WTBIO-{self.serial:07d}';mass=.07 if species=='field_mouse' else .16
        plant=self.tree.acct('plant',habitat);chem=self.tree.acct('chem',habitat)
        if self.book.mass[plant]<mass or self.book.energy[chem]<.025:return None
        self._convert([(plant,f'live:{id}',mass)])
        self.book.move(energy=[(chem,f'animal:{id}',.025)])
        actor=CohortAnimal(id,species,habitat,self.rng.choice('FM'),age=self.rng.randrange(20,100) if initial else 0,parent=parent,energy=.025)
        self.actors[id]=actor;self._log('introduced' if initial else 'birth',actor=id,species=species,habitat=habitat,parent=parent)
        return actor
    def _death(self,a,cause):
        if not a.alive:return
        mass=self.book.mass[f'live:{a.id}'];energy=self.book.energy[f'animal:{a.id}']
        if mass>0:self._convert([(f'live:{a.id}',self.tree.acct('detritus',a.habitat),mass)])
        if energy>0:self.book.move(energy=[(f'animal:{a.id}','environment:heat',energy)])
        a.alive=False;self._log('death',actor=a.id,cause=cause,species=a.species)
    def step(self,tick):
        if tick!=self.day+1:raise AssertionError('bridge clock mismatch')
        self.day=tick
        if self.tree.state not in ('active','germinating'):
            for a in self.actors.values():
                if a.alive:self._death(a,'world_tree_collapse')
            return
        for a in list(self.actors.values()):
            if not a.alive:continue
            a.age+=1
            e=f'animal:{a.id}';available=self.book.energy[e]
            burn=min(available, .00065 if self.juvenile_energy_conservation and a.parent is not None and a.age<=80 else .001)
            if burn:self.book.move(energy=[(e,'environment:heat',burn)])
            if a.species=='ridge_hound':
                prey=[b for b in self.actors.values() if b.alive and b.species in PREY[a.species] and b.habitat==a.habitat]
                if prey and self.rng.random()<.18:
                    victim=self.rng.choice(prey);v_mass=self.book.mass[f'live:{victim.id}'];v_energy=self.book.energy[f'animal:{victim.id}']
                    self.book.move(material=[(f'live:{victim.id}',f'live:{a.id}',v_mass*.3)])
                    self._convert([(f'live:{victim.id}',self.tree.acct('detritus',a.habitat),v_mass*.7)])
                    if v_energy>0:self.book.move(energy=[(f'animal:{victim.id}',e,v_energy*.65),(f'animal:{victim.id}','environment:heat',v_energy*.35)])
                    victim.alive=False;self._log('predation',predator=a.id,prey=victim.id)
            else:
                plant=self.tree.acct('plant',a.habitat);chem=self.tree.acct('chem',a.habitat)
                if self.book.mass[plant]>.04 and self.book.energy[chem]>.002:
                    self._convert([(plant,f'live:{a.id}',.002)])
                    self.book.move(energy=[(chem,e,.002)])
                    self._log('feeding',actor=a.id,habitat=a.habitat,plant_mass=.002)
            if self.book.energy[e]<.0005 or a.age>400:
                self._death(a,'starvation' if self.book.energy[e]<.0005 else 'age')
            elif a.age>80 and self.day%35==0 and self.rng.random()<.15:
                mates=[b for b in self.actors.values() if b.alive and b.species==a.species and b.sex!=a.sex and b.habitat==a.habitat and b.age>80]
                if mates:
                    if self.parental_investment:
                        from reproduction_021109 import birth_with_parental_investment
                        birth_with_parental_investment(self,a)
                    else:self._new(a.species,a.habitat,parent=a.id)
        self.book.audit()
    def report(self):
        return {s:sum(a.alive and a.species==s for a in self.actors.values()) for s in SPECIES}
