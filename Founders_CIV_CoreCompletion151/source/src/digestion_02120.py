"""A-019 opt-in, *synthetic* digestible tissue-energy pilot.

All energy is transferred on the existing WORLD-023 Book: plant meals debit
habitat chemical energy; animal tissue and maternal stocks receive funded energy;
hunting/scavenging move and dissipate existing embodied energy. No implicit
calorie creation, no second clock. Native World Tree residents still use their
own unmodified scheduler and are NOT assigned tissue-energy by this adapter.
"""
from __future__ import annotations
from collections import Counter
from species_life_02115 import HabitatBridge215, LifeBookAdapter, PROFILES, PREY
from tissue_energy_02120 import fund_tissue, digest, move_carcass, decay

PLANT_DIGESTIBILITY = .55
CARRION_DIGESTIBILITY = .78
MEAT_DIGESTIBILITY = .80
HUNT_COST = .00020

class EmbodiedBookAdapter(LifeBookAdapter):
    def tissue(self,a): return f'tissue_energy:{a.id}'
    def maternal_energy(self,a): return f'maternal_energy:{a.id}'
    def carrion_energy(self,habitat): return f'carrion_energy:tree:{self.bridge.tree.id}:{habitat}'

    def birth(self,mom,child,mass):
        maternal_mass = self.book.mass[self.maternal(mom)]
        maternal_energy = self.book.energy[self.maternal_energy(mom)]
        # Compute prior to maternal mass debit; offspring may inherit only what
        # is actually in the mother's existing energetic stock.
        inherited = maternal_energy * min(1.0,mass/max(maternal_mass,1e-12))
        prior_reserve=self.book.energy[self.reserve(mom)]
        if not super().birth(mom,child,mass): return False
        self.bridge.fluxes['offspring_reserve_energy_funded'] += prior_reserve-self.book.energy[self.reserve(mom)]
        self.bridge.fluxes['offspring_material_mass_funded'] += mass
        if inherited > 1e-12:
            self.book.move(energy=[(self.maternal_energy(mom),self.tissue(child),inherited)])
            self.bridge.fluxes['offspring_embodied_inherited'] += inherited
        return True

class HabitatBridge220(HabitatBridge215):
    def __init__(self,tree,seed=9711,counts=None):
        self.fluxes=Counter()
        super().__init__(tree,seed=seed,counts=counts)
        self.physical=EmbodiedBookAdapter(self)

    def _new(self,species,habitat,initial=False,parent=None):
        a=super()._new(species,habitat,initial=initial,parent=parent)
        if a is not None:
            chem=self.tree.acct('chem',habitat)
            # Pilot bootstrap: structural energy is *paid from* chemical stock,
            # not assumed to be already represented by native plant biomass.
            for body_key,mass_key,rate in [('tissue_energy:',f'live:{a.id}',.06),
                                            ('maternal_energy:',f'maternal:{a.id}',.06)]:
                amount=min(self.book.mass[mass_key]*rate,max(0.,self.book.energy[chem]-.001))
                if amount>1e-12:
                    fund_tissue(self.book,chem,f'{body_key}{a.id}',amount)
                    self.fluxes['initial_embodied_funded']+=amount
        return a

    def _feed_stock(self,a,source,kind):
        b=self.book; p=PROFILES[a.species]; ph=self.physical
        carrion = (source==self.carrion(a.habitat))
        # Plant food requires real World Tree chemical energy. Carrion energy
        # is held on the Book under its own physical habitat account.
        chem=ph.chem(a)
        q=min(p.intake*.012,b.mass[source])
        if not carrion:q=min(q,max(0.,b.energy[chem]/.80))
        if q<.0004:return False
        initial_source_mass=b.mass[source]
        target=p.adult_mass()*(.35+.65*min(1.,a.age/p.maturity))
        growth=min(q*.17,max(0.,target-b.mass[ph.live(a)])) if a.age<p.maturity else 0.
        store=(min(q*.22,max(0.,p.maternal_cap()-b.mass[ph.maternal(a)]))
               if a.sex=='F' and a.stage=='adult' else 0.)
        rest=max(0.,q-growth-store)
        legs=[]
        for account,amount in ((ph.live(a),growth),(ph.maternal(a),store),(ph.gut(a),rest)):
            if amount>1e-12:legs.append((source,account,amount))
        ph.convert(legs)
        if carrion:
            origin=ph.carrion_energy(a.habitat)
            intake=min(b.energy[origin], b.energy[origin]*q/max(initial_source_mass,1e-12))
            efficiency=CARRION_DIGESTIBILITY
        else:
            origin=chem
            intake=min(b.energy[origin],q*.80)
            efficiency=PLANT_DIGESTIBILITY
        digestible=intake*efficiency
        tissue=digestible*growth/q
        maternal=digestible*store/q
        reserve=max(0.,digestible-tissue-maternal)
        heat=intake-digestible
        transfers=[(origin,dest,x) for dest,x in
                   ((ph.tissue(a),tissue),(ph.maternal_energy(a),maternal),
                    (ph.reserve(a),reserve),('environment:heat',heat)) if x>1e-12]
        if transfers:b.move(energy=transfers)
        gut=b.mass[ph.gut(a)]
        if gut>1e-12:ph.convert([(ph.gut(a),ph.detritus(a),gut)])
        self.fluxes[f'{kind}_intake_energy']+=intake
        self.fluxes[f'{kind}_digestible_energy']+=digestible
        self.fluxes[f'{kind}_heat']+=heat
        self._log('feeding',actor=a.id,habitat=a.habitat,food_source=kind,mass=q,
                  growth=growth,maternal_mass=store,energy_intake=intake,
                  energy_digested=digestible,energy_to_heat=heat)
        return True

    def _hunt(self,a):
        # No hunting at zero energy: an attempted strike must afford its cost.
        if self.book.energy[self.physical.reserve(a)]<HUNT_COST:return False
        before=self.stats['hunt_attempt']
        caught=self.stats['predation']
        # Parent performs its native perception, escape, mass and reserve moves;
        # on success only *pre-existing* tissue-energy is partitioned below.
        victim_energy={x.id:(self.book.energy[f'tissue_energy:{x.id}'],
                             self.book.energy[f'maternal_energy:{x.id}'],
                             self.book.energy[f'animal:{x.id}'])
                       for x in self.actors.values() if x.alive and x.species in PREY[a.species]
                       and x.habitat==a.habitat}
        success=super()._hunt(a)
        if self.stats['hunt_attempt']>before:
            charged=min(HUNT_COST,self.book.energy[self.physical.reserve(a)])
            if charged>0:self.book.move(energy=[(self.physical.reserve(a),'environment:heat',charged)])
            self.fluxes['hunt_cost']+=charged
        if success and self.stats['predation']>caught:
            victim_id=self.events[-1]['prey']
            tissue,maternal,victim_reserve=victim_energy.get(victim_id,(0.,0.,0.))
            origin=f'tissue_energy:{victim_id}'; carcass=self.physical.carrion_energy(a.habitat)
            eaten=tissue*.30
            d=digest(self.book,origin,self.physical.reserve(a),eaten,MEAT_DIGESTIBILITY)
            gain,waste=d.assimilated,d.heat
            if tissue-eaten>1e-12:move_carcass(self.book,origin,carcass,tissue-eaten)
            if maternal>1e-12:move_carcass(self.book,f'maternal_energy:{victim_id}',carcass,maternal)
            self.fluxes['hunt_victim_reserve_energy_gained']+=victim_reserve*.65
            self.fluxes['hunt_victim_reserve_energy_heat']+=victim_reserve*.35
            self.fluxes['hunt_total_gross_energy_gained']+=gain+victim_reserve*.65
            self.fluxes['hunt_tissue_energy_gained']+=gain
            self.fluxes['hunt_tissue_energy_dissipated']+=waste
            self.fluxes['hunt_carcass_energy_left']+=tissue-eaten+maternal
            self._log('tissue_digestion',predator=a.id,prey=victim_id,
                      energy_gain=gain,energy_heat=waste,energy_carcass=tissue-eaten+maternal)
        return success

    def _death(self,a,cause):
        if not a.alive:return
        destination=(self.physical.carrion_energy(a.habitat)
                     if self.tree.state in ('active','germinating') else 'environment:heat')
        for origin in (f'tissue_energy:{a.id}',f'maternal_energy:{a.id}'):
            energy=self.book.energy[origin]
            if energy>1e-12:move_carcass(self.book,origin,destination,energy)
        super()._death(a,cause)

    def _decay(self):
        for habitat in self.tree.habitats:
            mass=self.book.mass[self.carrion(habitat)]
            if mass<=0:continue
            q=min(self.DECAY_RATE,mass)
            origin=self.physical.carrion_energy(habitat)
            energy=self.book.energy[origin]*q/mass
            if energy>1e-12:
                decay(self.book,origin,energy)
                self.fluxes['carcass_decay_energy_to_heat']+=energy
        super()._decay()

    def step(self,tick):
        super().step(tick)
        if self.tree.state not in ('active','germinating'):
            for habitat in self.tree.habitats:
                origin=self.physical.carrion_energy(habitat)
                energy=self.book.energy[origin]
                if energy>1e-12:self.book.move(energy=[(origin,'environment:heat',energy)])
            self.book.audit()

    def _check_registry(self):
        super()._check_registry()
        for a in self.actors.values():
            if not a.alive:
                assert self.book.energy[f'tissue_energy:{a.id}']<1e-8
                assert self.book.energy[f'maternal_energy:{a.id}']<1e-8

    def census(self):
        data=super().census()
        data['bridge_embodied_energy']=round(sum(
            self.book.energy[f'tissue_energy:{a.id}']+self.book.energy[f'maternal_energy:{a.id}']
            for a in self.actors.values()),9)
        data['habitat_carcass_energy']={p:round(self.book.energy[self.physical.carrion_energy(p)],9)
                                        for p in self.tree.habitats}
        data['food_energy_fluxes']={k:round(v,10) for k,v in sorted(self.fluxes.items())}
        return data
