"""U026-C003: opt-in, reserve-first autonomous provisioning for actual WORLD-024 Trees.

Tree metabolism/ecological death remains in WORLD-024. This policy only makes
physical Book transactions for portable food and finite creation-charge fruit.
No WorldBox game-side writes, no independent ledger, no automatic Founder spend.
All coefficients are synthetic hypotheses; enabled per experimental arm.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite

@dataclass
class ProvisionedLot:
    kind:str
    biome:str
    created:int
    state:str='stored'

class TreeProvisioningPolicy:
    def __init__(self,tree,food_period=8,fruit_period=12,maturity_days=5,
                 food_lifetime=20,fruit_lifetime=24,minimum_plant=2.5):
        # Reject fractional, Boolean and non-finite cadence values before
        # integer conversion. Truncation previously permitted zero periods,
        # producing a later modulo-by-zero after checkpoint advancement.
        periods=(food_period,fruit_period,maturity_days,food_lifetime,fruit_lifetime)
        if any(type(value) is not int or value <= 0 for value in periods):
            raise ValueError('periods and lifetimes must be positive integers')
        if maturity_days>=fruit_lifetime:raise ValueError('fruit lifetime must exceed maturity')
        # Reserve thresholds are physical quantities, not Boolean switches.
        # NaN silently bypasses comparisons and can authorize unfunded growth.
        if (isinstance(minimum_plant, bool) or
                not isinstance(minimum_plant, (int, float)) or
                not isfinite(minimum_plant) or minimum_plant < 0):
            raise ValueError('plant reserve must be finite and nonnegative')
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
        # A previous attempt may have committed this physical lot before a
        # later habitat allocation failed. Never publish it twice on retry.
        if lot in self.lots:return False
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
                    book.reserve_creation_charge(1.0,f'ce:reserve:{world_id}:{tree.id}:{tree.age}' if world_id is not None else f'ce:reserve:{tree.id}:{tree.age}')
                tree.grow_creation_fruit(biome,lot)
        self.lots[lot]=ProvisionedLot(kind,biome,tree.age)
        self.events.append(('grow',lot,tree.age))
        return True

    def tick(self):
        tree=self.tree
        # A detached Book cannot authorize production or age the policy state.
        # Fail before last_age, lot records, or any physical transaction changes.
        if tree.book is not tree.sim.book:
            raise ValueError('Tree provisioning requires authoritative simulation Book')
        # Reject invalid World namespaces before refreshing or aging existing
        # lots, not only when a new food/fruit lot happens to be produced.
        # This keeps malformed checkpoint identities from partially advancing.
        world_id=getattr(tree, 'world_id', None)
        if world_id is not None and (not isinstance(world_id, str) or not world_id or
                len(world_id)>64 or any(c not in
                'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in world_id)):
            raise ValueError('invalid World identity for physical lot')
        # Existing physical lots retain their original World namespace. A
        # reassigned Tree must not silently mix two World identities under
        # one policy/checkpoint (including after collapse).
        if self.lots:
            expected=(f'W-{world_id}-C003-{tree.id}-' if world_id is not None else f'C003-{tree.id}-')
            if any(not isinstance(lot, str) for lot in self.lots):
                raise ValueError('invalid Tree provisioned-lot checkpoint')
            if any(not lot.startswith(expected) for lot in self.lots):
                raise ValueError('World identity changed after physical lot production')
        # Reject corrupted habitat rotation before checkpoint or Book mutation.
        habitats=tuple(tree.habitats)
        if (not habitats or any(not isinstance(h, str) or not h or
                len(h)>64 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in h)
                for h in habitats) or len(set(habitats)) != len(habitats)):
            raise ValueError('invalid Tree habitat configuration')
        # Scheduler age is an observed nonnegative integer, never spendable time.
        # Reject corrupted checkpoint clocks before changing lots or Book state.
        if type(tree.age) is not int or tree.age < 0:
            raise ValueError('Tree age must be a nonnegative integer checkpoint')
        # Check restored lot chronology and habitat ownership before any
        # refresh/decay transaction. Future-dated or foreign-habitat lots
        # indicate a corrupt checkpoint, not goods eligible for recycling.
        for lot, rec in self.lots.items():
            # Check record shape and exact lot identity before accessing fields.
            # A corrupt restored checkpoint must fail closed, not throw an
            # AttributeError or accidentally operate on another Book account.
            if (not isinstance(lot, str) or not lot.startswith(
                    f'W-{world_id}-C003-{tree.id}-' if world_id is not None
                    else f'C003-{tree.id}-') or
                    type(rec) is not ProvisionedLot):
                raise ValueError('invalid Tree provisioned-lot checkpoint')
            expected_lot=(f'W-{world_id}-C003-{tree.id}-{rec.kind}-{rec.created}'
                          if world_id is not None else
                          f'C003-{tree.id}-{rec.kind}-{rec.created}')
            if lot != expected_lot:
                raise ValueError('invalid Tree provisioned-lot checkpoint')
            if (type(rec.created) is not int or rec.created < 0 or
                    rec.created > tree.age or rec.biome not in habitats or
                    rec.kind not in ('food', 'fruit') or
                    rec.state not in ('stored', 'mature', 'transferred', 'decayed') or
                    (rec.kind == 'food' and rec.state == 'mature')):
                raise ValueError('invalid Tree provisioned-lot checkpoint')
        # Restored checkpoint age is a strict scheduler integer. A Boolean or
        # fractional last_age can otherwise compare equal to a real day and
        # silently skip physical production or decay without a Book entry.
        if type(self.last_age) is not int or self.last_age < -1:
            raise ValueError('invalid Tree provisioning checkpoint age')
        if tree.age==self.last_age:return False
        if tree.age<self.last_age:raise ValueError('Tree age reversed; restore consistent checkpoint')
        # Refresh can fail closed on a physical Book operation. Do not mark
        # the age complete before lot maturity/decay succeeds, or retry after
        # checkpoint restoration would silently skip that day.
        # Existing physical lots continue aging after Tree collapse. Only new
        # production requires a living, stable Tree; archived remnants may
        # mature or decay without minting any matter or Creation Energy.
        # A refresh can decay several lots. Treat their Book transfers and
        # policy records as one retryable checkpoint operation; otherwise a
        # later failure leaves earlier decay/events committed on the same age.
        # A scheduler day is one physical Book action: decay and all habitat
        # allocations must commit together, or the same day remains retryable.
        # Restore local lot identity/state and events if any later allocation
        # rejects, including after an earlier allocation succeeded.
        prior_lots=dict(self.lots)
        prior_states={lot:rec.state for lot,rec in self.lots.items()}
        event_count=len(self.events)
        try:
            with tree.book.atomic_batch():
                self._refresh()
                if tree.state!='active' or tree.sim.seeds.plants[tree.id]['status']!='stable':
                    self.last_age=tree.age
                    return False
                if tree.age%self.food_period==0:
                    idx=(tree.age//self.food_period-1)%len(habitats)
                    self._allocate('food',habitats[idx])
                if tree.age%self.fruit_period==0:
                    idx=(tree.age//self.fruit_period-1)%len(habitats)
                    self._allocate('fruit',habitats[idx])
        except Exception:
            self.lots.clear()
            self.lots.update(prior_lots)
            for lot,state in prior_states.items():
                self.lots[lot].state=state
            del self.events[event_count:]
            raise
        self.last_age=tree.age
        return True

    def mature_fruit(self):
        tree=self.tree
        return [lot for lot,rec in self.lots.items() if rec.kind=='fruit' and
                rec.state=='mature' and tree.book.mass[f'fruit:lot:{lot}:tree:{tree.id}']>0]
