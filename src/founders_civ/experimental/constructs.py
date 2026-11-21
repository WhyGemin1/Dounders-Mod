"""Energy-maintained physical objects and dimensions, using the v0.18 Book.
Maintenance is energy movement, not material transformation and pays no toll.
Funded collapse performs exactly one material-state transition with a toll.
"""
from __future__ import annotations
from dataclasses import dataclass,field
from ..core.ledger import Book

@dataclass
class Construct:
    id:str
    kind:str
    host:str
    mass:float
    daily_energy:float
    integrity:float=1.0
    status:str='stable'
    collapse_to:str='remnant'
    inhabitants:set[str]=field(default_factory=set)
    events:list[dict]=field(default_factory=list)

class ConstructRegistry:
    def __init__(self,book:Book):
        self.book=book;self.items={};self.events=[]

    def build(self,id,kind,host,material_account,mass,daily_energy,
              initial_reserve,binding_energy=2.,collapse_to='remnant',work_source='world_work'):
        if id in self.items or kind not in ('construct','dimension'):
            raise ValueError('duplicate or invalid construct')
        if min(mass,daily_energy,initial_reserve,binding_energy)<0 or mass==0 or binding_energy<.3:
            raise ValueError('invalid construct resources')
        if collapse_to not in ('remnant','mist','inert'):
            raise ValueError('unknown collapse state')
        if work_source=='house' or self.book.energy[work_source]<1.:
            raise ValueError('construction work requires a funded non-House source')
        if self.book.energy['house']<initial_reserve+binding_energy:
            raise ValueError('not enough House energy')
        # These are sequential source debits but prechecked; a real main-engine
        # adapter should wrap build and ownership in one cross-registry transaction.
        self.book.transform([(material_account,f'construct:{id}',mass)],
                            source=work_source,work=1.,
                            energy_outputs=[(work_source,'environment:heat',.9)])
        q=initial_reserve+binding_energy
        if q>0:
            self.book.move(energy=[('house',f'reserve:{id}',initial_reserve),
                                   ('house',f'binding:{id}',binding_energy)] if initial_reserve>0
                           else [('house',f'binding:{id}',binding_energy)])
        c=Construct(id,kind,host,mass,daily_energy,collapse_to=collapse_to)
        self.items[id]=c
        self.events.append(dict(event='build',id=id,kind=kind,host=host))
        return c

    def top_up(self,id,amount,source='house',request_id=None):
        c=self.items[id]
        if c.status!='stable' or amount<=0:raise ValueError('invalid maintenance top-up')
        legs=[(source,f'reserve:{id}',amount)]
        if request_id is None:
            self.book.move(energy=legs)
            fresh=True
        else:
            _,fresh=self.book.move_once(request_id,energy=legs)
        if fresh:
            self.events.append(dict(event='top_up',id=id,amount=amount))
        return fresh

    def tick(self,id):
        c=self.items[id]
        if c.status!='stable':return c.status
        demand=c.daily_energy
        reserve=self.book.energy[f'reserve:{id}']
        paid=min(reserve,demand)
        if paid>0:self.book.move(energy=[(f'reserve:{id}','environment:heat',paid)])
        if demand>0 and paid+.0000001<demand:
            c.integrity=max(0,c.integrity-(demand-paid)/demand*.4)
            self.events.append(dict(event='maintenance_shortfall',id=id,deficit=demand-paid,integrity=c.integrity))
        elif demand>0:
            c.integrity=min(1,c.integrity+.05)
        if c.integrity<=0:
            self.collapse(id)
        return c.status

    def collapse(self,id):
        c=self.items[id]
        if c.status!='stable':return False
        source=f'binding:{id}'
        if self.book.energy[source]<.25:
            # Defers rather than violating funded transform rule. This should not
            # happen when bound energy is reserved correctly at build time.
            raise ValueError('binding energy exhausted; cannot fund collapse')
        self.book.transform([(f'construct:{id}',f'{c.collapse_to}:{id}',c.mass)],
                            source=source,work=.25,
                            energy_outputs=[(source,'environment:heat',.225)])
        for acct in (f'reserve:{id}',f'binding:{id}'):
            rem=self.book.energy[acct]
            if rem>0:self.book.move(energy=[(acct,'environment:heat',rem)])
        c.status='collapsed'; c.integrity=0
        self.events.append(dict(event='collapse',id=id,remaining_hazard=list(sorted(c.inhabitants)),
                                resultant_material=f'{c.collapse_to}:{id}'))
        return True
