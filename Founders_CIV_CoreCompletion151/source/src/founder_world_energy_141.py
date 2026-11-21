"""Cycle141 optional Founder-financed World Tree power commitment.

The Book conserves all energy, and existing Founder social states decide who is
eligible to sponsor a world. This layer does NOT mint sunlight, chemical food,
or animal reserves. A Founder-funded transfer to tree SUN can drive producer
work through the native World Tree's existing photosynthetic pathway.

This is a mechanically tested *authorization proxy*, not yet a full voluntary
proposal/decision episode in CommonsWorld's social scheduler. Such decisions
must be integrated as a distinct policy before canonical promotion.

Historically scaled synthetic energy units are not calibrated joules.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from math import isfinite

@dataclass(frozen=True)
class WorldEnergyFunding141:
    # Initial Founder contribution *in addition* to legacy world planting cost.
    creation_endowment:float = 6.0
    # Do not strip founders of their core operating energy.
    founder_floor:float = 1.05
    # Each founder can fund only a bounded amount at one decision episode.
    max_contribution:float = .42
    # Ongoing demand is for World production capacity, NOT animal reserves.
    critical_sun:float = .84
    critical_chem:float = 1.10
    # Artificial upper bounds prevent runaway financing even with many Founders.
    upkeep_per_habitat:float = .35
    upkeep_total:float = 1.05
    # Contributions become available for world processing; assessment is annualized
    # in days as an engineering sampling interval, not a time-credit allowance.
    inspection_every_days:int = 1
    def __post_init__(self):
        if any(not isfinite(x) or x < 0 for x in
               (self.creation_endowment,self.founder_floor,self.max_contribution,
                self.critical_sun,self.critical_chem,self.upkeep_per_habitat,self.upkeep_total)):
            raise ValueError('invalid funding coefficients')
        if self.max_contribution <= 0 or self.inspection_every_days < 1:
            raise ValueError('invalid funding policy')

class FounderWorldSupport141:
    """Single-Book Founder-backed World Tree endowment and shortage maintenance.

    All transfers are made in one Book atomic transaction. No donor override
    is allowed, and the registration of Founder contributions does not change
    a Founder's energy by itself.
    """
    def __init__(self,engine, policy=None):
        self.engine=engine
        self.policy=policy or WorldEnergyFunding141()
        self.totals=Counter()
        self.events=[]
        self.last_funding_day=None
        self.activation_complete=False
        self.creation_txn=None

    @property
    def world(self): return self.engine.bridge.tree
    @property
    def society(self): return self.engine.host.sim
    @property
    def book(self): return self.engine.host.book

    def _donors(self):
        world=self.world; soc=self.society; book=self.book; p=self.policy
        # The World owner gets first invitation; the social world's documented
        # _eligible_volunteer() gates all other candidates.
        names=[world.owner]+sorted(x for x in soc.founders.people if x!=world.owner)
        eligible=[]
        for fid in names:
            founder=soc.founders.people[fid]
            if not founder.alive:continue
            if not soc._eligible_volunteer(fid,world):continue
            available=max(0.,book.energy[f'founder:{fid}']-p.founder_floor)
            if available>1e-10:eligible.append((fid,available))
        return eligible

    def _contribute(self,amounts, target, purpose):
        if not amounts:return False
        if target not in self.world.habitats:raise ValueError('unknown habitat')
        if purpose not in ('creation','maintenance'):raise ValueError('purpose')
        # Every account is a real energy account in the existing shared Book.
        # Explicit preflight: don't partially fund when multiple donors are used.
        donors=self._donors();eligible={fid:balance for fid,balance in donors}
        for fid,q in amounts:
            if q<=0 or q>self.policy.max_contribution+1e-10 or eligible.get(fid,0.)+1e-10<q:
                raise ValueError('unfunded Founder contribution')
        legs=[(f'founder:{fid}',self.world.acct('sun',target),q) for fid,q in amounts]
        book=self.book; before=book.audit()
        txn=book.move(energy=legs)
        after=book.audit()
        assert abs(after['energy_error']-before['energy_error'])<1e-6
        total=sum(q for _,q in amounts)
        self.totals[f'{purpose}_contributions']+=len(amounts)
        self.totals[f'{purpose}_energy']+=total
        self.events.append({'day':self.engine.days,'purpose':purpose,'habitat':target,
                            'contributors':[fid for fid,_ in amounts], 'energy':total,
                            'book_seq':txn.seq})
        return txn

    def _allocate(self,energy, donors):
        """Use at most one capped contribution from each Founder per payment."""
        p=self.policy;remaining=energy;funded=[]
        for fid,available in donors:
            q=min(remaining,available,p.max_contribution)
            if q>1e-10:funded.append((fid,q));remaining-=q
            if remaining<=1e-9:break
        return funded,remaining

    def activate(self):
        if self.activation_complete:raise RuntimeError('already initialized')
        p=self.policy;tree=self.world
        if tree.state not in ('active','germinating'):raise RuntimeError('world not active')
        habitats=tuple(tree.habitats)
        # Founder endowment MUST be fully available; no partial activation.
        # All legs in a single transaction, distributed over active habitats.
        donors=self._donors()
        amounts,unfunded=self._allocate(p.creation_endowment,donors)
        if unfunded>1e-8:raise ValueError('World requires more Founder-backed creation energy')
        destinations={h:[] for h in habitats}
        # Slices of each pledge are assigned to habitats. The pledge itself is
        # bounded by one Founder policy decision; splitting is Book bookkeeping.
        for fid,q in amounts:
            for h in habitats:destinations[h].append((fid,q/len(habitats)))
        legs=[(f'founder:{fid}',tree.acct('sun',h),q)
              for h,payments in destinations.items() for fid,q in payments if q>1e-12]
        pre=self.book.audit();txn=self.book.move(energy=legs);post=self.book.audit()
        assert abs(pre['energy_error']-post['energy_error'])<1e-6
        self.totals['creation_contributions']=len(amounts)
        self.totals['creation_energy']=sum(q for _,q in amounts)
        self.creation_txn=txn.seq
        self.events.append({'day':self.engine.days,'purpose':'creation',
                            'habitats':list(habitats),'contributors':[fid for fid,_ in amounts],
                            'energy':sum(q for _,q in amounts),'book_seq':txn.seq})
        self.activation_complete=True
        return sum(q for _,q in amounts)

    def maintain(self):
        if not self.activation_complete:raise RuntimeError('world funding not initialized')
        day=self.engine.days+1
        if self.last_funding_day==day:return 0.
        self.last_funding_day=day
        p=self.policy
        if day%p.inspection_every_days:return 0.
        if self.world.state not in ('active','germinating'):return 0.
        book=self.book;remaining=p.upkeep_total
        paid=0.
        for h in tuple(self.world.habitats):
            sun=book.energy[self.world.acct('sun',h)]
            chem=book.energy[self.world.acct('chem',h)]
            # The trigger detects low World PRODUCTION energy, not an animal's
            # hunger wallet. No fuel is transferred directly to an animal.
            if sun>=p.critical_sun and chem>=p.critical_chem:continue
            needed=max(0.,p.critical_sun-sun)
            if chem<p.critical_chem:needed=max(needed,.12)
            amount=min(needed,p.upkeep_per_habitat,remaining)
            if amount<=1e-10:continue
            available=self._donors()
            allocations,unfunded=self._allocate(amount,available)
            if not allocations:
                self.totals['maintenance_unfunded_habitats']+=1
                continue
            self._contribute(allocations,h,'maintenance')
            delivered=sum(q for _,q in allocations)
            remaining-=delivered;paid+=delivered
            if unfunded>1e-8:self.totals['maintenance_shortfall']+=unfunded
            if remaining<=1e-9:break
        if paid<=1e-10:self.totals['no_maintenance_needed_or_available']+=1
        return paid

    def report(self):
        return {'status':'experimental_founder_funded_world_production',
                'contract':'Founder energy -> World sun -> producer energy, never directly into animal reserves',
                'totals':dict(self.totals),'creation_txn':self.creation_txn,
                'events':list(self.events[-12:])}
