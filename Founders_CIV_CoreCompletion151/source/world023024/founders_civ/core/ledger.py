"""Founders-CIV v0.17 strict atomic material/energy ledger.

One authoritative mass register, independent energy register; units are synthetic.
Explicit state transformation toll only, no toll for ownership/location moves.
The book is *not* a thermodynamic chemistry model: there is no elemental stoichiometry.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
from contextlib import contextmanager
import math

EPS=1e-7
TOLL=.10

@dataclass(frozen=True)
class Transaction:
    seq:int
    kind:str
    material:tuple
    energy:tuple
    toll:float
    external:float
    operation_id:str|None=None

class Book:
    def __init__(self):
        self.mass=defaultdict(float)
        self.energy=defaultdict(float)
        self.start_mass=None
        self.start_energy=None
        self.external=0.
        self.seq=0
        self.transactions=0
        self.toll_count=0
        self.rejected=0
        self.max_abs_mass_error=0.
        self.max_abs_energy_error=0.
        self.last=None
        # Part of the authoritative Book: no independent fruit/CE spend ledger.
        self.operations={}  # operation ID -> (canonical transaction signature, Transaction)
        self.asset_ids=set()  # unique, permanently retired identifiers

    def seed_mass(self,key,value):
        assert self.start_mass is None and value>=0 and math.isfinite(value)
        self.mass[key]+=value

    def seed_energy(self,key,value):
        assert self.start_energy is None and value>=0 and math.isfinite(value)
        self.energy[key]+=value

    def freeze(self):
        self.start_mass=sum(self.mass.values())
        self.start_energy=sum(self.energy.values())

    def apply(self,kind,material=(),energy=(),toll=0.,external=0.,operation_id=None,asset_id=None):
        """Prevalidate complete deltas, commit atomically; failures mutate no state."""
        material=tuple(tuple(v) for v in material)
        energy=tuple(tuple(v) for v in energy)
        try:
            # Idempotency and identity checks happen before balance checks: a
            # correctly retried transfer must not fail because it spent its source.
            for value,label in ((operation_id,'operation ID'),(asset_id,'asset ID')):
                if value is not None and (not isinstance(value,str) or not value or len(value)>128):
                    raise ValueError('invalid '+label)
            if asset_id is not None and operation_id is None:
                raise ValueError('unique assets require an operation ID')
            # Preserve exact binary-float identities for replay signatures.
            # Rounding to 12 decimals could silently accept a different amount
            # as an idempotent retry, even though no transfer was performed.
            def stable_legs(legs):
                return tuple((src,dst,float(q).hex()) for src,dst,q in legs)
            signature=(kind,stable_legs(material),stable_legs(energy),
                       float(toll).hex(),float(external).hex(),asset_id)
            # Validate quantities even on a replay. NaN/Infinity must never
            # bypass validation through a previously accepted operation ID.
            if any(not math.isfinite(float(q)) or float(q) <= 0
                   for legs in (material, energy) for _, _, q in legs):
                raise ValueError('invalid transfer quantity')
            if not all(math.isfinite(float(x)) for x in (toll, external)):
                raise ValueError('invalid toll or inflow')
            if operation_id is not None and operation_id in self.operations:
                prior_sig, prior_txn = self.operations[operation_id]
                if prior_sig!=signature:raise ValueError('conflicting operation ID replay')
                return prior_txn
            if asset_id is not None and asset_id in self.asset_ids:
                raise ValueError('duplicate permanent asset identity')
            if kind not in {'move','ingest','transform','wellspring','reserve_ce'}:
                raise ValueError('unknown transaction')
            if self.start_mass is None:raise ValueError('seed ledger before usage')
            if not (math.isfinite(toll) and math.isfinite(external)) or toll<0 or external<0:raise ValueError('invalid toll or inflow')
            if kind!='transform' and toll:raise ValueError('nontransform toll')
            if kind=='move' and any(str(s).split(':',1)[0]!=str(t).split(':',1)[0] for s,t,q in material):
                raise ValueError('material-state change requires a funded transform transaction')
            if kind=='ingest':
                # One food lot to one specific gut, with paired embodied
                # energy. Ingestion is physical relocation, not digestion.
                # Reject mismatched materials/energy, actors and food sources.
                if len(material)!=1 or len(energy)!=1:
                    raise ValueError('ingestion must transfer one paired edible lot')
                src,dst,q=material[0]
                esrc,edst,eq=energy[0]
                mtyp,_,msuffix=str(src).partition(':')
                etyp,_,esuffix=str(esrc).partition(':')
                dtyp,_,dsuffix=str(dst).partition(':')
                detyp,_,desuffix=str(edst).partition(':')
                energy_for={'plant':'edible_energy', 'carrion':'carrion_energy',
                            'detritus':'detritus_energy', 'portable_food':'food_energy'}
                gut_for={'gut':'gut_energy','gut_native':'gut_energy_native'}
                if (mtyp not in energy_for or etyp!=energy_for[mtyp] or
                    msuffix!=esuffix or dtyp not in gut_for or
                    detyp!=gut_for[dtyp] or dsuffix!=desuffix or
                    q<=0 or eq<=0):
                    raise ValueError('mismatched food, embedded energy or gut owner')
            if kind=='reserve_ce':
                # The existing river_pool represents the finite, fictional
                # energy source. Reclassification is *not* a Wellspring mint.
                if (material or len(energy)!=1 or energy[0][0]!='river_pool'
                        or energy[0][1]!='ce:river' or toll or external):
                    raise ValueError('creation charge reservation must debit river_pool')
            if kind=='transform':
                if not any(str(s).split(':',1)[0]!=str(t).split(':',1)[0] for s,t,q in material):
                    raise ValueError('a transformation must change material state')
                if toll<=0:raise ValueError('transform must pay a toll')
            if kind=='wellspring' and (material or energy or external<=0):raise ValueError('invalid Wellspring entry')
            if kind!='wellspring' and external:raise ValueError('external source must be Wellspring')
            dm=defaultdict(float);de=defaultdict(float)
            for s,t,q in material:
                if s==t or q<=0 or not math.isfinite(q):raise ValueError('invalid material leg')
                dm[s]-=q;dm[t]+=q
            for s,t,q in energy:
                if s==t or q<=0 or not math.isfinite(q):raise ValueError('invalid energy leg')
                # CE is a typed sub-economy in the *same* Book. Ordinary
                # physics/biology cannot accidentally turn fruit charge into
                # heat or chemical fuel, or vice versa.
                if str(s).startswith('ce:') != str(t).startswith('ce:'):
                    if not (kind=='reserve_ce' and s=='river_pool' and t=='ce:river'):
                        raise ValueError('creation charge/biological energy type mismatch')
                de[s]-=q;de[t]+=q
            if kind=='wellspring':de['house']+=external
            if abs(sum(dm.values()))>EPS or abs(sum(de.values())-external)>EPS:raise ValueError('unbalanced transaction')
            # EPS is an audit tolerance, never permission to create stock.
            # Reject even sub-EPS overdrafts before any mutation.
            if any(self.mass.get(k,0.)+v < 0 for k,v in dm.items()):raise ValueError('material overdraw')
            for key, delta in de.items():
                prior = self.energy.get(key, 0.)
                if prior + delta < 0:
                    raise ValueError(f'energy overdraw {key}: balance={prior!r} '
                                     f'delta={delta!r} deficit={-(prior+delta)!r}')
            if kind=='transform':
                # One toll may have multiple destination legs, but only 3 canonical sinks.
                splits=(sum(q for s,t,q in energy if t=='world_toll'),
                        sum(q for s,t,q in energy if t=='underworld:0'),
                        sum(q for s,t,q in energy if t=='house'))
                if any(abs(a-b)>EPS for a,b in zip(splits,(toll*.2,toll*.1,toll*.7))):
                    raise ValueError('bad toll allocation')
            for k,v in dm.items():self.mass[k]=max(0.,self.mass[k]+v)
            for k,v in de.items():self.energy[k]=max(0.,self.energy[k]+v)
            self.external+=external
            self.seq+=1;self.transactions+=1
            if kind=='transform':self.toll_count+=1
            self.last=Transaction(self.seq,kind,material,energy,toll,external,operation_id)
            if operation_id is not None:
                self.operations[operation_id]=(signature,self.last)
            if asset_id is not None:self.asset_ids.add(asset_id)
            return self.last
        except (ValueError,AssertionError):
            self.rejected+=1
            raise

    @contextmanager
    def atomic_batch(self):
        """Roll back an interrupted composite Book operation as one unit.

        Used only when several *Book* transactions form one physical action.
        The caller must defer non-Book side effects until this context exits.
        This is not a shadow ledger: the same Book object is restored in place.
        """
        stocks=(self.mass.copy(),self.energy.copy())
        journal=(self.operations.copy(),self.asset_ids.copy())
        counters=(self.external,self.seq,self.transactions,self.toll_count,
                  self.rejected,self.max_abs_mass_error,self.max_abs_energy_error,
                  self.last)
        try:
            yield self
        except Exception:
            self.mass.clear();self.mass.update(stocks[0])
            self.energy.clear();self.energy.update(stocks[1])
            self.operations.clear();self.operations.update(journal[0])
            self.asset_ids.clear();self.asset_ids.update(journal[1])
            (self.external,self.seq,self.transactions,self.toll_count,
             self.rejected,self.max_abs_mass_error,self.max_abs_energy_error,
             self.last)=counters
            self.rejected+=1
            raise

    def move(self,material=(),energy=(),operation_id=None):
        return self.apply('move',material,energy,operation_id=operation_id)

    def reserve_creation_charge(self, amount, operation_id):
        """Reserve finite river energy as fictional CE; never mint from rest.

        The river_pool -> ce:river conversion is an explicit, audited
        provisional semantic mapping until the U026 river model is completed.
        """
        return self.apply('reserve_ce',energy=[('river_pool','ce:river',amount)],
                          operation_id=operation_id)

    def ingest(self, material, energy, operation_id=None):
        """Atomic, fee-free relocation of already edible food into gut.

        This does not perform digestion, produce usable fuel, or mint resources.
        Only typed physical food and matching embodied-energy accounts may
        participate; ordinary cross-state moves still require transforms.
        """
        return self.apply('ingest', material, energy,operation_id=operation_id)

    def transform(self,material,source,work,energy_outputs=(),operation_id=None,asset_id=None):
        """Work is debited from source; caller routes work minus toll to sinks.
        Additional non-work energy transfers (e.g. plant chemical to food chemical) are allowed.
        """
        if str(source).startswith('ce:'):raise ValueError('CE cannot be used as chemical work')
        if work<=0 or not math.isfinite(work):raise ValueError('work must be positive')
        toll=TOLL*work
        # Construct an exact source debit in the same accumulation order as
        # apply(). Separately rounded 60/30/2/1/7 percent legs can exceed a
        # fully funded work balance by one ULP (e.g. 2.64 -> 2.6400000000000006).
        # Assign that rounding remainder to the final House toll leg, rather
        # than allowing even a tiny unfunded overdraft or clamping a balance.
        legs=list(energy_outputs)+[(source,'world_toll',toll*.2),
                                   (source,'underworld:0',toll*.1)]
        source_delta=0.
        for leg_source, _, amount in legs:
            if leg_source==source:
                source_delta-=amount
        house_toll_share=work+source_delta
        # The binary-float accumulator in Book.apply can round the last
        # subtraction upward by one ULP of *work*, even though all work was
        # funded. Choose the greatest representable House leg whose combined
        # debit does not exceed the declared work. This is independent of
        # current account balances, so an exact checkpoint replay keeps its
        # original transaction signature; genuine overdrafts still reject.
        # Only the final toll leg absorbs representational roundoff.
        for _ in range(64):
            combined=0.
            for leg_source, _, amount in legs:
                if leg_source==source:
                    combined-=amount
            combined-=house_toll_share
            if house_toll_share>0 and -combined<=work:
                break
            if house_toll_share<=0:
                raise ValueError('unfunded House toll leg')
            house_toll_share=math.nextafter(house_toll_share,0.)
        else:
            raise ValueError('cannot represent funded House toll leg')
        legs.append((source,'house',house_toll_share))
        # Enforce caller's declared work output, disallow hidden work energy.
        if abs(sum(q for s,t,q in energy_outputs if s==source)-(work-toll))>EPS:
            raise ValueError('work output not funded')
        return self.apply('transform',material,legs,toll=toll,
                          operation_id=operation_id,asset_id=asset_id)

    def wellspring(self,q,operation_id=None):return self.apply('wellspring',external=q,operation_id=operation_id)

    def audit(self):
        m=sum(self.mass.values())-self.start_mass
        e=sum(self.energy.values())-(self.start_energy+self.external)
        self.max_abs_mass_error=max(self.max_abs_mass_error,abs(m))
        self.max_abs_energy_error=max(self.max_abs_energy_error,abs(e))
        mass_tolerance=max(EPS,1e-10*self.start_mass)
        energy_tolerance=max(EPS,1e-10*(self.start_energy+self.external))
        if abs(m)>mass_tolerance or abs(e)>energy_tolerance:
            raise AssertionError(f'ledger error mass={m}, energy={e}')
        if min(self.mass.values(), default=0.) < -EPS or min(self.energy.values(), default=0.) < -EPS:
            raise AssertionError('negative stock')
        return {'mass_error':m,'energy_error':e,'max_abs_mass_error':self.max_abs_mass_error,
                'max_abs_energy_error':self.max_abs_energy_error,'mass_total':sum(self.mass.values()),
                'energy_total':sum(self.energy.values()),'external_wellspring':self.external,
                'transactions':self.transactions,'toll_events':self.toll_count,'rejections':self.rejected,
                'idempotent_operations':len(self.operations),'unique_assets':len(self.asset_ids)}
