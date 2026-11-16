"""U026-C003: opt-in, reserve-first autonomous provisioning for actual WORLD-024 Trees.

Tree metabolism/ecological death remains in WORLD-024. This policy only makes
physical Book transactions for portable food and finite creation-charge fruit.
No WorldBox game-side writes, no independent ledger, no automatic Founder spend.
All coefficients are synthetic hypotheses; enabled per experimental arm.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class ProvisionedLot:
    kind:str
    biome:str
    created:int
    state:str='stored'

class TreeProvisioningPolicy:
    def __init__(self,tree,food_period=8,fruit_period=12,maturity_days=5,
                 food_lifetime=20,fruit_lifetime=24,minimum_plant=2.5):
        if min(food_period,fruit_period,maturity_days,food_lifetime,fruit_lifetime)<=0:
            raise ValueError('periods and lifetimes must be positive')
        if maturity_days>=fruit_lifetime:raise ValueError('fruit lifetime must exceed maturity')
        if minimum_plant<0:raise ValueError('negative plant reserve')
        self.tree=tree
        self.food_period=int(food_period)
        self.fruit_period=int(fruit_period)
        self.maturity_days=int(maturity_days)
        self.food_lifetime=int(food_lifetime)
        self.fruit_lifetime=int(fruit_lifetime)
        self.minimum_plant=float(minimum_plant)
        self.lots={}
        self.last_age=-1
        self.events=[]

    def _reserve(self,biome,need,food=False):
        tree=self.tree;book=tree.book
        if tree.state!='active':return False
        if tree.sim.seeds.plants[tree.id]['status']!='stable':return False
        residents=sum(r.alive and r.habitat==biome for r in tree.residents.values())
        # Protect an explicit ecological reserve that scales with local mouths.
        reserve=max(self.minimum_plant,1.0 + .5*residents)
        if book.mass[tree.acct('plant',biome)] < reserve+need+1e-9:return False
        if book.energy[tree.acct('sun',biome)]<(.008 if food else .01):return False
        if food and book.energy[tree.acct('chem',biome)]<.02:return False
        return True

    def _refresh(self):
        tree=self.tree;book=tree.book
        for lot,rec in list(self.lots.items()):
            if rec.state not in ('stored','mature'):continue
            prefix='portable_food' if rec.kind=='food' else 'fruit'
            account=f'{prefix}:lot:{lot}:tree:{tree.id}'
            if book.mass[account]<1e-9:
                rec.state='transferred'
                continue
            age=tree.age-rec.created
            if rec.kind=='fruit' and age>=self.maturity_days and rec.state=='stored':
                rec.state='mature';self.events.append(('mature',lot,tree.age))
            lifetime=self.food_lifetime if rec.kind=='food' else self.fruit_lifetime
            if age<lifetime:continue
            sun=tree.acct('sun',rec.biome)
            work=.004 if rec.kind=='food' else .005
            # A collapsed Tree can leave unharvested goods as remnants; do not
            # invent energy to decompose them after sunlight is exhausted.
            if book.energy[sun]<work:continue
            ops=tree.resources
            if rec.kind=='food':ops.decay_food(rec.biome,lot)
            else:ops.decay_fruit(rec.biome,lot)
            rec.state='decayed';self.events.append(('decay',lot,tree.age))

    def _allocate(self,kind,biome):
        tree=self.tree;book=tree.book
        amount=.08 if kind=='food' else .10
        if not self._reserve(biome,amount,kind=='food'):return False
        # A World namespace, when assigned by the global scheduler, is part of
        # the physical lot identity carried through Book accounts, harvest,
        # exchange, ingestion and replay. Preserve old checkpoint identities
        # for legacy single-World Trees without an explicit namespace.
        world_id=getattr(tree, 'world_id', None)
        if world_id is not None:
            if (not isinstance(world_id, str) or not world_id or
                len(world_id)>64 or any(c not in
                'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in world_id)):
                raise ValueError('invalid World identity for physical lot')
            lot=f'W-{world_id}-C003-{tree.id}-{kind}-{tree.age}'
        else:
            lot=f'C003-{tree.id}-{kind}-{tree.age}'
        if kind=='food':
            tree.make_portable_food(biome,lot)
        else:
            # CE reservation and physical fruit growth are ONE composite
            # Book action. If fruit growth rejects after the reservation,
            # restore the finite river pool, CE and all operation identities.
            # No lot/event is published until the Book batch commits.
            with book.atomic_batch():
                if book.energy['ce:river'] < 1.-1e-9:
                    if book.energy['river_pool']<1.-1e-9:return False
                    book.reserve_creation_charge(1.0,f'ce:reserve:{tree.id}:{tree.age}')
                tree.grow_creation_fruit(biome,lot)
        self.lots[lot]=ProvisionedLot(kind,biome,tree.age)
        self.events.append(('grow',lot,tree.age))
        return True

    def tick(self):
        tree=self.tree
        if tree.age==self.last_age:return False
        if tree.age<self.last_age:raise ValueError('Tree age reversed; restore consistent checkpoint')
        self.last_age=tree.age
        if tree.state!='active' or tree.sim.seeds.plants[tree.id]['status']!='stable':return False
        self._refresh()
        # Deterministic habitat rotation, never an artificial time currency.
        habitats=tuple(tree.habitats)
        if tree.age%self.food_period==0:
            idx=(tree.age//self.food_period-1)%len(habitats)
            self._allocate('food',habitats[idx])
        if tree.age%self.fruit_period==0:
            idx=(tree.age//self.fruit_period-1)%len(habitats)
            self._allocate('fruit',habitats[idx])
        return True

    def mature_fruit(self):
        tree=self.tree
        return [lot for lot,rec in self.lots.items() if rec.kind=='fruit' and
                rec.state=='mature' and tree.book.mass[f'fruit:lot:{lot}:tree:{tree.id}']>0]
