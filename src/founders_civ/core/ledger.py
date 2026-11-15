"""Founders-CIV v0.17 strict atomic material/energy ledger.

One authoritative mass register, independent energy register; units are synthetic.
Explicit state transformation toll only, no toll for ownership/location moves.
The book is *not* a thermodynamic chemistry model: there is no elemental stoichiometry.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
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
        # Same authoritative Book owns replay receipts; no secondary SQLite ledger.
        self.request_receipts={}

    def seed_mass(self,key,value):
        assert self.start_mass is None and value>=0 and math.isfinite(value)
        self.mass[key]+=value

    def seed_energy(self,key,value):
        assert self.start_energy is None and value>=0 and math.isfinite(value)
        self.energy[key]+=value

    def freeze(self):
        self.start_mass=sum(self.mass.values())
        self.start_energy=sum(self.energy.values())

    def apply(self,kind,material=(),energy=(),toll=0.,external=0.):
        """Prevalidate complete deltas, commit atomically; failures mutate no state."""
        material=tuple(tuple(v) for v in material)
        energy=tuple(tuple(v) for v in energy)
        try:
            if kind not in {'move','ingest','transform','wellspring'}:raise ValueError('unknown transaction')
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
                            'detritus':'detritus_energy'}
                gut_for={'gut':'gut_energy','gut_native':'gut_energy_native'}
                if (mtyp not in energy_for or etyp!=energy_for[mtyp] or
                    msuffix!=esuffix or dtyp not in gut_for or
                    detyp!=gut_for[dtyp] or dsuffix!=desuffix or
                    q<=0 or eq<=0):
                    raise ValueError('mismatched food, embedded energy or gut owner')
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
                de[s]-=q;de[t]+=q
            if kind=='wellspring':de['house']+=external
            if abs(sum(dm.values()))>EPS or abs(sum(de.values())-external)>EPS:raise ValueError('unbalanced transaction')
            if any(self.mass[k]+v < -EPS for k,v in dm.items()):raise ValueError('material overdraw')
            if any(self.energy[k]+v < -EPS for k,v in de.items()):raise ValueError('energy overdraw')
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
            self.last=Transaction(self.seq,kind,material,energy,toll,external)
            return self.last
        except (ValueError,AssertionError):
            self.rejected+=1
            raise

    def move(self,material=(),energy=()):
        return self.apply('move',material,energy)

    def move_once(self, request_id, material=(), energy=()):
        """Idempotent Book move. Receipt and stock update share one in-memory commit.

        Request receipts survive deepcopy/pickle of this Book. They do NOT prove
        external disk checkpoint atomicity or native WorldBox acknowledgement.
        """
        if not isinstance(request_id, str) or not request_id.strip():
            raise ValueError('nonempty request id required')
        legs = (tuple(tuple(x) for x in material),
                tuple(tuple(x) for x in energy))
        previous = self.request_receipts.get(request_id)
        if previous is not None:
            prior_legs, receipt = previous
            if prior_legs != legs:
                raise ValueError('request id reused with different transfer')
            return receipt, False
        # apply prevalidates and commits the complete Book move. No receipt
        # is written if it rejects; no untracked second resource authority.
        receipt = self.move(material=legs[0], energy=legs[1])
        self.request_receipts[request_id] = (legs, receipt)
        return receipt, True

    def ingest(self, material, energy):
        """Atomic, fee-free relocation of already edible food into gut.

        This does not perform digestion, produce usable fuel, or mint resources.
        Only typed physical food and matching embodied-energy accounts may
        participate; ordinary cross-state moves still require transforms.
        """
        return self.apply('ingest', material, energy)

    def transform(self,material,source,work,energy_outputs=()):
        """Work is debited from source; caller routes work minus toll to sinks.
        Additional non-work energy transfers (e.g. plant chemical to food chemical) are allowed.
        """
        if work<=0 or not math.isfinite(work):raise ValueError('work must be positive')
        toll=TOLL*work
        legs=list(energy_outputs)+[(source,'world_toll',toll*.2),(source,'underworld:0',toll*.1),
                                    (source,'house',toll*.7)]
        # Enforce caller's declared work output, disallow hidden work energy.
        if abs(sum(q for s,t,q in energy_outputs if s==source)-(work-toll))>EPS:
            raise ValueError('work output not funded')
        return self.apply('transform',material,legs,toll=toll)

    def wellspring(self,q):return self.apply('wellspring',external=q)

    def audit(self):
        m=sum(self.mass.values())-self.start_mass
        e=sum(self.energy.values())-(self.start_energy+self.external)
        self.max_abs_mass_error=max(self.max_abs_mass_error,abs(m))
        self.max_abs_energy_error=max(self.max_abs_energy_error,abs(e))
        mass_tolerance=max(EPS,1e-10*self.start_mass)
        energy_tolerance=max(EPS,1e-10*(self.start_energy+self.external))
        if abs(m)>mass_tolerance or abs(e)>energy_tolerance:
            raise AssertionError(f'ledger error mass={m}, energy={e}')
        if min(self.mass.values()) < -EPS or min(self.energy.values()) < -EPS:
            raise AssertionError('negative stock')
        return {'mass_error':m,'energy_error':e,'max_abs_mass_error':self.max_abs_mass_error,
                'max_abs_energy_error':self.max_abs_energy_error,'mass_total':sum(self.mass.values()),
                'energy_total':sum(self.energy.values()),'external_wellspring':self.external,
                'transactions':self.transactions,'toll_events':self.toll_count,'rejections':self.rejected}
