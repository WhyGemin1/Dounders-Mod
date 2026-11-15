"""v0.21.14 EXPERIMENTAL habitat encounter and physical carrion adapter.

Maintains the existing WORLD-023/024 Book and time clock; does NOT claim to
implement v0.21.7 life history or calibrated predator-prey parameters.
The original v0.21.13 implementation remains available for paired comparisons.
"""
from collections import Counter
from habitat_bridge import HabitatBridge, SPECIES, PREY


class HabitatBridge214(HabitatBridge):
    TRAVEL_COST = .00035
    DECAY_RATE = .006

    def __init__(self, tree, seed=9711, counts=None):
        super().__init__(tree, seed=seed, counts=counts)
        self._check_registry()

    def _convert(self,legs):
        """Fund conversions after real tree collapse (which drains sunlight).

        Do not use House directly as transform source: its canonical toll sends
        70% back to House and the Book forbids self-transfer. Use an intermediate
        work account, funded by an actual House energy debit.
        """
        work=.0001
        source=self.tree.acct('sun','forest')
        if self.book.energy[source]+1e-10<work:
            if self.book.energy['house']+1e-10<work:
                raise ValueError('bridge conversion lacks sunlight and House work reserve')
            source=f'work:habitat_bridge:{self.tree.id}'
            self.book.move(energy=[('house',source,work)])
        return self.book.transform(legs,source=source,work=work,
                energy_outputs=[(source,'environment:heat',.9*work)])

    def carrion(self, habitat):
        return f'carrion:tree:{self.tree.id}:{habitat}'

    def _check_registry(self):
        """A single view of distinct WORLD-023 and bridge agents.

        This does not put bridge agents into the legacy resident reproductive
        scheduler or duplicate body material accounts.
        """
        assert set(self.actors).isdisjoint(self.tree.residents)
        for a in self.actors.values():
            assert a.habitat in self.tree.habitats
            stock = self.book.mass[f'live:{a.id}']
            assert stock >= 0 and (a.alive or stock < 1e-7)
        for r in self.tree.residents.values():
            assert r.habitat in self.tree.habitats
            stock = self.book.mass[f'body:{r.id}']
            assert stock >= 0 and (r.alive or stock < 1e-7)

    def census(self):
        bridge = self.report()
        return {
            'bridge_species': bridge,
            'bridge_total': sum(bridge.values()),
            'world023_residents': self.tree.population,
            'combined_unique': sum(bridge.values()) + self.tree.population,
            'distinct_biological_schedulers': 2,
        }

    def _migrate(self, a):
        """Adjacent-only travel funded by the actor's existing energy reserve."""
        current=a.habitat
        neighbors=tuple(self.tree.habitats[current].neighbors)
        if not neighbors:return False
        energy=f'animal:{a.id}'
        if self.book.energy[energy] < self.TRAVEL_COST + .0005:return False
        alive=[x for x in self.actors.values() if x.alive]
        destination=None
        reason=None
        if a.species in PREY:
            counts=Counter(x.habitat for x in alive if x.species in PREY[a.species])
            if counts[current]==0:
                better=max(neighbors,key=lambda p:(counts[p],p))
                if counts[better]>0:destination=better;reason='prey_encounter'
                elif self.day%7==0:destination=self.rng.choice(neighbors);reason='explore'
        elif a.species=='carrion_bird':
            here=self.book.mass[self.carrion(current)]
            better=max(neighbors,key=lambda p:(self.book.mass[self.carrion(p)],p))
            if self.book.mass[self.carrion(better)]>here+.012:
                destination=better;reason='carrion_encounter'
        else:
            grazers=Counter(x.habitat for x in alive if x.species not in PREY and x.species!='carrion_bird')
            plant=lambda p:self.book.mass[self.tree.acct('plant',p)]/(1+grazers[p])
            if plant(current)<.22:
                better=max(neighbors,key=lambda p:(plant(p),p))
                if plant(better)>plant(current)*1.25:
                    destination=better;reason='forage_pressure'
        if destination is None:return False
        self.book.move(energy=[(energy,'environment:heat',self.TRAVEL_COST)])
        a.habitat=destination
        self._log('migration',actor=a.id,species=a.species,from_habitat=current,
                  to_habitat=destination,reason=reason,energy_cost=self.TRAVEL_COST)
        return True

    def _death(self,a,cause):
        """Dead body and reserves stay in-tree, or become collapse remnants."""
        if not a.alive:return
        mass=self.book.mass[f'live:{a.id}']
        en=self.book.energy[f'animal:{a.id}']
        if mass>0:
            if self.tree.state in ('active','germinating'):
                dest=self.tree.acct('detritus',a.habitat)
            else:
                dest=f'remnant:tree:{self.tree.id}:{a.habitat}'
            self._convert([(f'live:{a.id}',dest,mass)])
        if en>0:self.book.move(energy=[(f'animal:{a.id}','environment:heat',en)])
        a.alive=False
        self._log('death',actor=a.id,cause=cause,species=a.species,habitat=a.habitat)

    def _hunt(self,a):
        candidates=[x for x in self.actors.values() if x.alive and x.species in PREY[a.species]
                    and x.habitat==a.habitat]
        if not candidates or self.rng.random()>=.18:return False
        victim=self.rng.choice(candidates)
        v_mass=self.book.mass[f'live:{victim.id}']
        v_energy=self.book.energy[f'animal:{victim.id}']
        # Require a funded carcass transformation before moving any material.
        if v_mass>0:
            self.book.move(material=[(f'live:{victim.id}',f'live:{a.id}',v_mass*.3)])
            self._convert([(f'live:{victim.id}',self.carrion(a.habitat),v_mass*.7)])
        if v_energy>0:self.book.move(energy=[(f'animal:{victim.id}',f'animal:{a.id}',v_energy*.65),
                                             (f'animal:{victim.id}','environment:heat',v_energy*.35)])
        victim.alive=False
        self._log('death',actor=victim.id,cause='predation',species=victim.species,habitat=victim.habitat)
        self._log('predation',predator=a.id,prey=victim.id,habitat=a.habitat,
                  prey_mass=v_mass,carcass_mass=v_mass*.7)
        return True

    def _feed_scavenger(self,a):
        carrion=self.carrion(a.habitat)
        chem=self.tree.acct('chem',a.habitat)
        source=carrion if self.book.mass[carrion]>.0004 else self.tree.acct('plant',a.habitat)
        q=.002 if source==carrion else .0007  # optional seed/fruit fallback
        if self.book.mass[source]<q or self.book.energy[chem]<.001:return False
        self._convert([(source,f'live:{a.id}',q)])
        self.book.move(energy=[(chem,f'animal:{a.id}',.001)])
        self._log('feeding',actor=a.id,habitat=a.habitat,
                  food_source='carrion' if source==carrion else 'plant_fallback',mass=q)
        return True

    def _feed_herbivore(self,a):
        plant=self.tree.acct('plant',a.habitat)
        chem=self.tree.acct('chem',a.habitat)
        if self.book.mass[plant]<=.04 or self.book.energy[chem]<=.002:return False
        self._convert([(plant,f'live:{a.id}',.002)])
        self.book.move(energy=[(chem,f'animal:{a.id}',.002)])
        self._log('feeding',actor=a.id,habitat=a.habitat,food_source='plant',mass=.002)
        return True

    def _decay(self):
        for habitat in self.tree.habitats:
            from_account=self.carrion(habitat)
            mass=self.book.mass[from_account]
            if mass<=0:continue
            q=min(self.DECAY_RATE,mass)
            self._convert([(from_account,self.tree.acct('detritus',habitat),q)])
            self._log('decomposition',habitat=habitat,mass=q)

    def step(self,tick):
        if tick!=self.day+1:raise AssertionError('bridge clock mismatch')
        self.day=tick
        if self.tree.state not in ('active','germinating'):
            for a in self.actors.values():
                if a.alive:self._death(a,'world_tree_collapse')
            for p in self.tree.habitats:
                q=self.book.mass[self.carrion(p)]
                if q:self._convert([(self.carrion(p),f'remnant:tree:{self.tree.id}:{p}',q)])
            self.book.audit();self._check_registry()
            return
        for a in list(self.actors.values()):
            if not a.alive:continue
            a.age+=1
            self._migrate(a)
            energy=f'animal:{a.id}'
            q=min(.001,self.book.energy[energy])
            if q:self.book.move(energy=[(energy,'environment:heat',q)])
            if a.species in PREY:self._hunt(a)
            elif a.species=='carrion_bird':self._feed_scavenger(a)
            else:self._feed_herbivore(a)
            if self.book.energy[energy]<.0005 or a.age>400:
                self._death(a,'starvation' if self.book.energy[energy]<.0005 else 'age')
            elif a.age>80 and self.day%35==0 and self.rng.random()<.15:
                mates=[b for b in self.actors.values() if b.alive and b.species==a.species
                       and b.sex!=a.sex and b.habitat==a.habitat and b.age>80]
                if mates:self._new(a.species,a.habitat,parent=a.id)
        self._decay()
        self.book.audit()
        self._check_registry()
