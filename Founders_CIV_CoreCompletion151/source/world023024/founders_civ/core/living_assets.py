"""U026 C002: Book-funded Tree food and creation-charge fruit operations.

These methods operate on the *actual* WORLD-024 WorldTree and its sim.book.
They do not replace Tree ecology or provide WorldBox gameplay commands.
All coefficients are synthetic; maturity, automatic harvest policy and new
World spawning are assigned to later development cycles.
"""
from __future__ import annotations
import re
import math

_ID=re.compile(r'^[A-Za-z0-9_.-]{1,64}$')


def _identifier(value, name):
    if not isinstance(value,str) or not _ID.fullmatch(value):
        raise ValueError('invalid '+name)
    return value


def _positive(value, name):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not (0 < value < 1e12):
        raise ValueError('invalid '+name)
    return float(value)


class TreeResourceOps:
    """Application layer over a single, physically authoritative Core151 Book.

    Operation/asset identity is committed *inside Book.apply*, not in a second
    ledger. The World Tree must be active to produce goods; the goods remain
    owned by a Founder even if their source Tree subsequently collapses.
    """
    def __init__(self, tree):
        self.tree=tree
        self.book=tree.sim.book

    def _active(self,biome):
        if self.tree.state!='active' or self.tree.sim.seeds.plants[self.tree.id]['status']!='stable':
            raise ValueError('inactive Tree cannot produce goods')
        if biome not in self.tree.habitats:
            raise ValueError('unknown Tree habitat')

    def _founder(self,founder):
        _identifier(founder,'founder')
        if founder not in self.tree.sim.founders.people:
            raise ValueError('unknown Founder')

    def _account(self,prefix,lot,owner_type,owner):
        return f'{prefix}:lot:{lot}:{owner_type}:{owner}'

    def _complete_lot(self,material_source,energy_source,biomass,charge,operation_id):
        """A fruit/food ID is transferred whole; never silently split its owner.

        Existing operations replay from Book's committed signature, even after
        the source account has been emptied. This is an ownership invariant,
        not an action-energy restriction.
        """
        if operation_id in self.book.operations:
            return
        if (abs(self.book.mass.get(material_source,0.) - biomass)>1e-8
                or abs(self.book.energy.get(energy_source,0.) - charge)>1e-8):
            if self.book.mass.get(material_source,0.) < 1e-8 or self.book.energy.get(energy_source,0.) < 1e-8:
                raise ValueError('material overdraw or unavailable identified lot')
            raise ValueError('identified lot must transfer in full')

    def make_food(self,biome,lot,biomass=.08,chemical=.02,work=.008):
        """Package local plant and existing chemical energy as portable food.

        A food lot starts owned by its Tree, not magically in a Founder gut.
        The named lot ID stays unique even after consumption or decay.
        """
        _identifier(lot,'food lot')
        if f'food:make:{self.tree.id}:{lot}' not in self.book.operations:
            self._active(biome)
        biomass=_positive(biomass,'biomass');chemical=_positive(chemical,'chemical energy')
        work=_positive(work,'packaging work')
        src=self.tree.acct('sun',biome)
        return self.book.transform(
            material=[(self.tree.acct('plant',biome),self._account('portable_food',lot,'tree',self.tree.id),biomass)],
            source=src,work=work,
            energy_outputs=[(src,self.tree.acct('heat',biome),.90*work),
                (self.tree.acct('chem',biome),self._account('food_energy',lot,'tree',self.tree.id),chemical)],
            operation_id=f'food:make:{self.tree.id}:{lot}',asset_id=f'food:{lot}')

    def harvest_food(self,lot,founder,biomass=.08,chemical=.02):
        _identifier(lot,'food lot');self._founder(founder)
        biomass=_positive(biomass,'biomass');chemical=_positive(chemical,'chemical energy')
        operation=f'food:harvest:{lot}:{founder}'
        self._complete_lot(self._account('portable_food',lot,'tree',self.tree.id),
                           self._account('food_energy',lot,'tree',self.tree.id),
                           biomass,chemical,operation)
        return self.book.move(
            material=[(self._account('portable_food',lot,'tree',self.tree.id),
                       self._account('portable_food',lot,'founder',founder),biomass)],
            energy=[(self._account('food_energy',lot,'tree',self.tree.id),
                     self._account('food_energy',lot,'founder',founder),chemical)],
            operation_id=operation)

    def eat_food(self,lot,founder,biomass=.08,chemical=.02):
        """Ingest, not digest. Eating does not immediately recharge a Founder."""
        _identifier(lot,'food lot');self._founder(founder)
        biomass=_positive(biomass,'biomass');chemical=_positive(chemical,'chemical energy')
        operation=f'food:ingest:{lot}:{founder}'
        self._complete_lot(self._account('portable_food',lot,'founder',founder),
                           self._account('food_energy',lot,'founder',founder),
                           biomass,chemical,operation)
        return self.book.ingest(
            material=[(self._account('portable_food',lot,'founder',founder),f'gut:founder:{founder}:lot:{lot}',biomass)],
            energy=[(self._account('food_energy',lot,'founder',founder),f'gut_energy:founder:{founder}:lot:{lot}',chemical)],
            operation_id=operation)

    def grow_fruit(self,biome,lot,biomass=.10,creation_charge=1.0,work=.01):
        """Consume real plant biomass and reserved river CE to form fruit.

        The limited `ce:river` account is funded only by audited reservation of
        the existing `river_pool`. It is not duplicated per Tree.
        """
        _identifier(lot,'fruit lot')
        if f'fruit:grow:{self.tree.id}:{lot}' not in self.book.operations:
            self._active(biome)
        biomass=_positive(biomass,'fruit biomass')
        creation_charge=_positive(creation_charge,'creation charge')
        work=_positive(work,'fruit work')
        src=self.tree.acct('sun',biome)
        return self.book.transform(
            material=[(self.tree.acct('plant',biome),self._account('fruit',lot,'tree',self.tree.id),biomass)],
            source=src,work=work,
            energy_outputs=[(src,self.tree.acct('heat',biome),.9*work),
                ('ce:river',self._account('ce:fruit',lot,'tree',self.tree.id),creation_charge)],
            operation_id=f'fruit:grow:{self.tree.id}:{lot}',asset_id=f'fruit:{lot}')

    def harvest_fruit(self,lot,founder,biomass=.10,creation_charge=1.0):
        _identifier(lot,'fruit lot');self._founder(founder)
        biomass=_positive(biomass,'fruit biomass');creation_charge=_positive(creation_charge,'creation charge')
        operation=f'fruit:harvest:{lot}:{founder}'
        self._complete_lot(self._account('fruit',lot,'tree',self.tree.id),
                           self._account('ce:fruit',lot,'tree',self.tree.id),
                           biomass,creation_charge,operation)
        return self.book.move(
            material=[(self._account('fruit',lot,'tree',self.tree.id),
                       self._account('fruit',lot,'founder',founder),biomass)],
            energy=[(self._account('ce:fruit',lot,'tree',self.tree.id),
                     self._account('ce:fruit',lot,'founder',founder),creation_charge)],
            operation_id=operation)

    def fund_world_seed(self,lot,founder,seed,biomass=.10,creation_charge=1.0,work=.01):
        """Fund a virtual seed. Not a native WorldBox world or live planting.

        A Founder may always *propose* a world; this is the explicit funding
        transition that spends fruit. The river work cost is not an action timer.
        """
        _identifier(lot,'fruit lot');self._founder(founder);_identifier(seed,'seed')
        biomass=_positive(biomass,'seed biomass')
        creation_charge=_positive(creation_charge,'seed creation charge')
        work=_positive(work,'seed shaping work')
        operation=f'seed:fund:{seed}'
        self._complete_lot(self._account('fruit',lot,'founder',founder),
                           self._account('ce:fruit',lot,'founder',founder),
                           biomass,creation_charge,operation)
        return self.book.transform(
            material=[(self._account('fruit',lot,'founder',founder),f'world_seed:{seed}',biomass)],
            source=f'founder:{founder}',work=work,
            energy_outputs=[(f'founder:{founder}',f'creation_heat:{seed}',.9*work),
                (self._account('ce:fruit',lot,'founder',founder),f'ce:seed:{seed}',creation_charge)],
            operation_id=operation,asset_id=f'seed:{seed}')

    def decay_food(self, biome, lot, biomass=.08, chemical=.02, work=.004):
        """Recycle unharvested Tree-owned food, keeping both matter and energy.

        Harvested lots are never decayed by the Tree. Replay is Book-idempotent.
        """
        _identifier(lot, 'food lot'); biomass=_positive(biomass,'biomass')
        chemical=_positive(chemical,'chemical energy');work=_positive(work,'decay work')
        if biome not in self.tree.habitats:raise ValueError('unknown Tree habitat')
        operation=f'food:decay:{self.tree.id}:{lot}'
        source=self._account('portable_food',lot,'tree',self.tree.id)
        esource=self._account('food_energy',lot,'tree',self.tree.id)
        self._complete_lot(source,esource,biomass,chemical,operation)
        sun=self.tree.acct('sun',biome)
        return self.book.transform(
            material=[(source,self.tree.acct('detritus',biome),biomass)],
            source=sun,work=work,
            energy_outputs=[(sun,self.tree.acct('heat',biome),.9*work),
                            (esource,self.tree.acct('heat',biome),chemical)],
            operation_id=operation)

    def decay_fruit(self, biome, lot, biomass=.10, creation_charge=1., work=.005):
        """Return biomass to detritus and unspent CE to the shared river reserve.

        CE remains a distinct conservation class; it never becomes chemical fuel.
        """
        _identifier(lot,'fruit lot');biomass=_positive(biomass,'biomass')
        creation_charge=_positive(creation_charge,'creation charge');work=_positive(work,'decay work')
        if biome not in self.tree.habitats:raise ValueError('unknown Tree habitat')
        operation=f'fruit:decay:{self.tree.id}:{lot}'
        source=self._account('fruit',lot,'tree',self.tree.id)
        esource=self._account('ce:fruit',lot,'tree',self.tree.id)
        self._complete_lot(source,esource,biomass,creation_charge,operation)
        sun=self.tree.acct('sun',biome)
        return self.book.transform(
            material=[(source,self.tree.acct('detritus',biome),biomass)],
            source=sun,work=work,
            energy_outputs=[(sun,self.tree.acct('heat',biome),.9*work),
                            (esource,'ce:river',creation_charge)],
            operation_id=operation)

    def digest_food(self, lot, founder):
        """Digest one previously ingested lot, without minting chemical energy.

        Synthetic partition: 0.08 gut matter -> 0.05 assimilated matter +
        0.03 waste; 0.02 gut chemical energy -> 0.015 usable chemical store,
        0.005 heat; a separately funded 0.001 metabolic work input
        produces 0.0009 heat and 0.0001 audited transformation toll. Digestion is
        separate from eating and does not immediately replenish action fuel.
        """
        _identifier(lot, 'food lot'); self._founder(founder)
        ingested=f'food:ingest:{lot}:{founder}'
        if ingested not in self.book.operations:
            raise ValueError('cannot digest food not ingested by this Founder')
        operation=f'food:digest:{lot}:{founder}'
        gut=f'gut:founder:{founder}:lot:{lot}'
        fuel=f'gut_energy:founder:{founder}:lot:{lot}'
        body=f'body_chemical:founder:{founder}'
        founder_pool=f'founder:{founder}'
        # The Book is authoritative for fuel and replay. Previously digested
        # food may fund later digestion; no energy is created by resting.
        # A replay MUST use its original funding source, even if balances
        # have since changed, to preserve the committed transaction signature.
        if operation in self.book.operations:
            previous=self.book.operations[operation][1]
            sources=[leg[0] for leg in previous.energy if leg[1]==f'body_heat:founder:{founder}' and abs(leg[2]-.0009)<1e-9]
            if len(sources)!=1:
                raise ValueError('invalid committed digestion work provenance')
            work_source=sources[0]
        elif self.book.energy[founder_pool]>=.001-1e-10:
            work_source=founder_pool
        elif self.book.energy[body]>=.001-1e-10:
            work_source=body
        else:
            raise ValueError('insufficient existing metabolic fuel for digestion')
        return self.book.transform(
            material=[(gut,f'assimilated:founder:{founder}',.05),
                      (gut,f'waste:founder:{founder}',.03)],
            source=work_source,work=.001,
            energy_outputs=[(fuel,body,.015),
                            (fuel,f'body_heat:founder:{founder}',.005),
                            (work_source,f'body_heat:founder:{founder}',.0009)],
            operation_id=operation)
