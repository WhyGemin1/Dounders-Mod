"""Cycle143 mainline core-completion candidate: one Book, two distinct populations.

Correct physical ingestion in both schedulers. Eating is a Book transfer of
*existing* food mass + embodied energy into gut storage, not an arbitrary
sunlight work toll; usable substrate appears only through later digestion.
World time remains an external coordinate, never an actor-owned currency.

Important: native residents retain their own demographic engine, while bridge
animals retain FivePhaseBridge142's different demographic scheduler.
Synthetic rate parameters are uncalibrated; do not promote without validation.
"""
from __future__ import annotations
from math import exp
from five_phase_core_142 import (
    UnifiedFivePhase142, FivePhaseBridge142, PairedWorldTree142,
    EdibleInventory142, PLANT_EDIBLE_ENERGY_DENSITY,
)

# Rate (world-days^-1) for native gut assimilation. This is deliberately a
# provisional rate and MUST be calibrated to species/diet data later.
NATIVE_ABSORPTION_RATE = 0.8
NATIVE_ASSIMILATION_FRACTION = .74
NATIVE_GUT_MASS_CAP = .16

class EdibleInventory143(EdibleInventory142):
    def ingest(self, animal, lot, mass, quality, name):
        """Ingestion does not charge sun or credit instantly available fuel.

        Locomotion/search work is already settled when a real movement resolves.
        Ingesting a successfully acquired food lot is *not* a second action toll.
        """
        b=self.bridge.book; br=self.bridge
        if lot.material=='producer_plant': self.balance(lot.habitat)
        q=min(max(0., mass), self.available_mass(lot))
        if q<1e-6:return False
        energy=q*lot.nominal_density
        if b.energy[lot.energy_account]+1e-10 < energy:return False
        txn=b.ingest(material=[(lot.mass_account,br.physical.gut(animal),q)],
                   energy=[(lot.energy_account,br._gut_energy(animal),energy)])
        s=br._state(animal)
        s.gut_energy_weight+=energy
        s.gut_quality_weight+=energy*quality
        br.physiology_metrics['ingested_mass']+=q
        br.physiology_metrics['ingested_energy']+=energy
        br.physiology_metrics['paired_lot_meals']+=1
        br.physiology_metrics['fee_free_ingestion']+=1
        if br.eco_flags.spatial:br._spend_forage_quota(animal,lot.mass_account,q)
        br._log('feeding',actor=animal.id,habitat=animal.habitat,
                food_source=name,mass=q,into_gut_energy=energy,
                absorbed_immediately=0.,book_seq=txn.seq)
        return True

class CoreCompletionWorld143(PairedWorldTree142):
    """Native residents share paired food lots and use delayed absorption."""
    def _native_gut(self,r):return f'gut_native:{r.id}'
    def _native_gut_energy(self,r):return f'gut_energy_native:{r.id}'

    def _feed(self,r):
        inventory=self._five_phase_inventory
        lot=inventory.plant(r.habitat)
        inventory.balance(r.habitat)
        b=self.book
        # Gut and structural fuel are distinct physical locations. Native
        # stomach capacity prevents unbounded, instant food acquisition.
        gut=self._native_gut(r)
        q=min(.06, max(0.,NATIVE_GUT_MASS_CAP-b.mass[gut]),
              inventory.available_mass(lot))
        if q<=.001:return False
        energy=q*lot.nominal_density
        txn=b.ingest(material=[(lot.mass_account,gut,q)],
                   energy=[(lot.energy_account,self._native_gut_energy(r),energy)])
        self.last_txn=txn
        self.counters['tree_grazing']+=1
        self.counters['native_gut_meals']+=1
        self._event('tree_native_ingest',actor=r.id,habitat=r.habitat,
                    mass=q,energy=energy,absorbed_immediately=0.,txn=txn)
        return True

    def _native_absorb(self,r):
        b=self.book
        gut=self._native_gut(r); ge=self._native_gut_energy(r)
        gm=b.mass[gut]
        if gm<=1e-12:return 0.
        # Native _animals feeds then metabolizes in the same day. Delayed
        # digestion means only this rate-limited fraction becomes available,
        # never the full ingested food reward at once.
        q=min(gm,gm*(1.-exp(-NATIVE_ABSORPTION_RATE)))
        if q<=1e-12:return 0.
        contained=b.energy[ge]
        e=min(contained,contained*q/gm)
        useful=e*NATIVE_ASSIMILATION_FRACTION
        heat=e-useful
        # Digestion changes the material state, unlike ingestion. Pay its
        # tiny reaction toll from existing native metabolism, never sun or
        # an intention/action point; absorbed fuel remains Book-backed.
        work=q*.0005
        met=f'metabolic:{r.id}'
        if b.energy[met]+1e-12<work:return 0.
        b.transform([(gut,f'fuel:{r.id}',q)],source=met,work=work,
            energy_outputs=[(met,self.acct('heat',r.habitat),work*.9),
                (ge,met,useful), (ge,self.acct('heat',r.habitat),heat)])
        self.counters['native_absorption_events']+=1
        self.counters['native_absorbed_energy']+=useful
        return useful

    def _metabolism(self,r):
        self._native_absorb(r)
        return super()._metabolism(r)

    def _death(self,r,cause):
        if not r.alive:return False
        # Do not strand undigested food when native residents die or the Tree
        # collapses; Book still owns these physical mass and energy amounts.
        b=self.book
        gut=self._native_gut(r);ge=self._native_gut_energy(r)
        mass=b.mass[gut];energy=b.energy[ge]
        transfers=[];en=[]
        if mass>0:transfers.append((gut,self.acct('detritus',r.habitat),mass))
        if energy>0:en.append((ge,f'detritus_energy:tree:{self.id}:{r.habitat}',energy))
        if transfers:
            src=self.acct('sun',r.habitat)
            work=.0001
            if b.energy[src]+1e-12<work:
                src=f'work:native_gut_release:{self.id}:{r.id}'
                if b.energy['house']>=work:b.move(energy=[('house',src,work)])
            if b.energy[src]>=work:
                b.transform(transfers,source=src,work=work,
                    energy_outputs=[(src,self.acct('heat',r.habitat),work*.9)]+en)
            else:
                # Preserve material in its original Book account rather than
                # violating conservation when physical decomposition is unfunded.
                self.counters['native_gut_decay_deferred']+=1
        elif en:b.move(energy=en)
        return super()._death(r,cause)

class CoreCompletionBridge143(FivePhaseBridge142):
    pass

class UnifiedCoreCompletion143(UnifiedFivePhase142):
    """Explicit continuation of the integrated Cycle142 engine; not a fork of ecology."""
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if type(self.bridge) is not FivePhaseBridge142:
            raise TypeError('Expected active Cycle142 bridge for migration')
        if type(self.bridge.tree) is not PairedWorldTree142:
            raise TypeError('Expected Cycle142 paired native population')
        self.bridge.__class__=CoreCompletionBridge143
        self.bridge.lots=EdibleInventory143(self.bridge)
        self.bridge.tree.__class__=CoreCompletionWorld143
        self.bridge.tree._five_phase_inventory=self.bridge.lots
        self.bridge.physiology_metrics['core_completion_143_active']+=1
        assert self.host.book is self.bridge.book is self.bridge.tree.book
        self.host.book.audit()

    def report(self):
        r=super().report()
        r['core_completion_143']={
            'status':'integrated_engine_candidate_not_canonical',
            'paired_ingestion_no_action_fee':True,
            'native_delayed_absorption':True,
            'one_world_clock':True,
            'separate_demographic_schedulers':True,
            'native_gut_meals':self.bridge.tree.counters['native_gut_meals'],
            'native_absorption_events':self.bridge.tree.counters['native_absorption_events'],
            'bridge_fee_free_meals':self.bridge.physiology_metrics['fee_free_ingestion'],
        }
        return r
