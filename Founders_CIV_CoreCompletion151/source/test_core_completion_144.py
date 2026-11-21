"""Actual Cycle144 code-level acceptance checks, not claims of ecology stability."""
import copy
import pickle
import unittest
from dataclasses import replace
from core_completion_144 import UnifiedCoreCompletion144, fraction_over_elapsed, WorldSupport144
from species_traits_143 import BLUEPRINTS, Phenotype143

class Cycle144Tests(unittest.TestCase):
    def setUp(self):
        self.s=UnifiedCoreCompletion144(seed=100001)
        self.br=self.s.bridge
        self.book=self.s.host.book

    def actor(self, species='forest_elephant'):
        return next(a for a in self.br.actors.values() if a.alive and a.species==species)

    def test_one_book_and_two_distinct_schedulers(self):
        self.assertIs(self.book,self.br.tree.book)
        self.assertIs(self.book,self.br.book)
        self.assertEqual(len(self.s.host.sim.founders.people),100)
        self.assertNotEqual(type(self.br),type(self.br.tree))
        self.assertEqual(self.book.audit()['rejections'],0)

    def test_complete_species_blueprints_and_nonidentical_individuals(self):
        self.assertEqual(len(BLUEPRINTS),13)
        self.assertEqual(set(BLUEPRINTS),{a.species for a in self.br.actors.values()})
        self.assertEqual(len(self.br.phenotypes),len(self.br.actors))
        rabbits=[self.br._trait(a) for a in self.br.actors.values() if a.species=='burrow_rabbit']
        self.assertGreater(len(set(rabbits)),1)

    def test_traits_affect_metabolic_demand_and_cost(self):
        a=self.actor()
        base=self.br.phenotypes[a.id]
        self.br.phenotypes[a.id]=replace(base,basal=.75)
        low=self.br._maintenance_demand(a)
        self.br.phenotypes[a.id]=replace(base,basal=1.40)
        high=self.br._maintenance_demand(a)
        self.assertGreater(high,low*1.7)
        self.book.audit()

    def test_traits_change_real_food_absorption_and_keep_conservation(self):
        a=self.actor()
        plant=self.br.tree.acct('plant',a.habitat)
        self.assertTrue(self.br._feed_stock(a,plant,'plant',dt=.25))
        slow=copy.deepcopy(self.s);fast=copy.deepcopy(self.s)
        ga=slow.bridge.actors[a.id];gb=fast.bridge.actors[a.id]
        ta=slow.bridge.phenotypes[a.id];tb=fast.bridge.phenotypes[a.id]
        slow.bridge.phenotypes[a.id]=replace(ta,digestion=.74)
        fast.bridge.phenotypes[a.id]=replace(tb,digestion=1.26)
        slow.bridge._digest(ga,.25);fast.bridge._digest(gb,.25)
        self.assertGreater(slow.host.book.mass[slow.bridge.physical.gut(ga)],
                           fast.host.book.mass[fast.bridge.physical.gut(gb)])
        slow.host.book.audit();fast.host.book.audit()

    def test_inheritance_uses_parent_phenotypes_and_real_maternal_stocks(self):
        mother=self.actor('burrow_rabbit')
        if mother.sex!='F':
            mother=next(x for x in self.br.actors.values() if x.species=='burrow_rabbit' and x.sex=='F')
        father=next(x for x in self.br.actors.values() if x.species==mother.species and x.sex=='M')
        childtraits_before=set(self.br.phenotypes)
        # Physically funded motherhood remains mandatory. A fixture may need
        # to transfer *existing* material/energy from donor habitat accounts.
        p=__import__('species_life_02115').PROFILES[mother.species]
        stock=self.br.physical.maternal(mother)
        needed=p.newborn_mass()
        shortage=max(0.,needed-self.book.mass[stock])
        if shortage:
            donor=self.br.tree.acct('plant',mother.habitat)
            self.book.move(material=[(donor,stock,shortage)])
        mother.pregnant_until=self.br.day
        mother.pregnancy_father=father.id
        born=self.br._birth(mother)
        self.assertGreater(born,0)
        additions=set(self.br.phenotypes)-childtraits_before
        self.assertEqual(len(additions),born)
        for uid in additions:
            child=self.br.actors[uid]
            self.assertEqual(child.parent,mother.id)
            self.assertEqual(child.generation,mother.generation+1)
            self.assertNotEqual(self.br.phenotypes[uid],Phenotype143())
        self.book.audit()

    def test_native_feeding_and_migration_not_old_chem_gate(self):
        r=next(x for x in self.br.tree.residents.values() if x.alive)
        tree=self.br.tree
        local=tree._five_phase_inventory.plant(r.habitat)
        self.assertGreaterEqual(tree._five_phase_inventory.available_mass(local),0)
        self.assertTrue(tree._feed(r))
        e=self.book.energy[tree._native_gut_energy(r)]
        self.assertGreater(e,0)
        tree._native_absorb(r)
        self.assertLess(self.book.energy[tree._native_gut_energy(r)],e)
        self.book.audit()

    def test_physical_world_stewardship_separate_from_producer_energy(self):
        self.assertIsInstance(self.s.world_support,WorldSupport144)
        world=self.br.tree
        c=self.s.host.sim.seeds.constructs.items[world.id]
        before_res=self.book.energy[f'reserve:{world.id}']
        before_sun=sum(self.book.energy[world.acct('sun',h)] for h in world.habitats)
        before_total=self.book.audit()['energy_total']
        self.s.world_support.maintain()
        after_res=self.book.energy[f'reserve:{world.id}']
        self.assertGreaterEqual(after_res, before_res)
        self.assertAlmostEqual(self.book.audit()['energy_total'], before_total,places=6)
        if after_res>before_res:
            self.assertGreater(self.s.world_support.totals['structure_energy'],0)
        self.assertGreaterEqual(sum(self.book.energy[world.acct('sun',h)] for h in world.habitats),0)

    def test_photosynthesis_physically_recharges_edible_mass(self):
        t=self.br.tree
        h='forest';lot=self.br.lots.plant(h)
        source=t.acct('sun',h)
        # Move all embodied food energy to its valid detritus destination,
        # forcing a shortage while preserving exactly the Book total.
        e=self.book.energy[lot.energy_account]
        if e>0:self.book.move(energy=[(lot.energy_account,
                 self.br.lots.detritus(h).energy_account,e)])
        self.br.lots._last_photo_age.pop(h,None)
        before_total=self.book.audit()['energy_total']
        before_sun=self.book.energy[source]
        self.assertGreater(before_sun,0.)
        self.br.lots.balance(h)
        gained=self.book.energy[lot.energy_account]
        self.assertGreater(gained,0.)
        self.assertLess(self.book.energy[source],before_sun)
        self.assertAlmostEqual(self.book.audit()['energy_total'],before_total,places=6)
        n=self.br.lots.metrics['photosynthetic_days']
        self.br.lots.balance(h)
        self.assertEqual(self.br.lots.metrics['photosynthetic_days'],n)

    def test_no_sunlight_no_free_production(self):
        t=self.br.tree;h='forest';lot=self.br.lots.plant(h)
        self.br.lots._last_photo_age.pop(h,None)
        sun=t.acct('sun',h)
        available=self.book.energy[sun]
        if available:self.book.move(energy=[(sun,'environment:heat',available)])
        # Superclass may still package existing chemical energy, but solar
        # capture must be zero when the actual Book solar account is empty.
        before=self.br.lots.metrics['photosynthetic_capture_energy']
        self.br.lots.balance(h)
        self.assertEqual(self.br.lots.metrics['photosynthetic_capture_energy'],before)
        self.book.audit()

    def test_long_term_reserve_refills_from_real_absorption(self):
        a=self.actor('forest_elephant');b=self.br;book=self.book
        target=b.physical.reserve(a)
        source=b.tree.acct('plant',a.habitat)
        # Ensure test begins with capacity to refill; debited energy remains in
        # the Book and does not appear as new fuel.
        current=book.energy[target]
        if current>0:book.move(energy=[(target,'environment:heat',current)])
        before=book.audit()['energy_total']
        for _ in range(4):
            b._feed_stock(a,source,'plant',dt=.25)
            b._digest(a,.25)
        self.assertGreater(book.energy[target],0.0)
        self.assertGreater(b.trait_metrics['nutrition_stored_to_reserve'],0.0)
        self.assertAlmostEqual(book.audit()['energy_total'],before,places=6)

    def test_cloud_water_returns_to_biomes_without_minting(self):
        tree=self.br.tree
        cloud=f'water:tree:{tree.id}:cloud'
        source=tree.acct('water','forest')
        # Move existing water into cloud; do not introduce new material.
        self.book.move(material=[(source,cloud,12.)])
        before_total=self.book.audit()['mass_total']
        before_cloud=self.book.mass[cloud]
        before=sum(self.book.mass[tree.acct('water',h)] for h in tree.habitats)
        tree._climate_and_plants()
        self.assertGreater(tree.counters['cloud_precipitation_mass'],0.)
        self.assertGreater(sum(self.book.mass[tree.acct('water',h)] for h in tree.habitats),0.)
        self.assertLess(self.book.mass[cloud],before_cloud+5.)
        self.assertAlmostEqual(self.book.audit()['mass_total'],before_total,places=6)

    def test_drought_shuts_off_convective_precipitation(self):
        t=self.br.tree
        cloud=f'water:tree:{t.id}:cloud'
        self.book.move(material=[(t.acct('water','forest'),cloud,12.)])
        t.precipitation_factor=0.0
        before=t.counters['cloud_precipitation_mass']
        t._climate_and_plants()
        self.assertEqual(t.counters['cloud_precipitation_mass'],before)
        self.book.audit()


        self.assertAlmostEqual(fraction_over_elapsed(.72,.25),1-__import__('math').exp(-.18))
        a=self.actor(); self.assertFalse(hasattr(a,'action_wallet'))
        self.assertFalse(hasattr(a,'time_budget'))
        before=self.book.seq
        self.br._choose(a)
        self.assertEqual(self.book.seq,before)

    def test_pickle_resume_and_five_day_replay(self):
        self.s.run(2)
        resumed=pickle.loads(pickle.dumps(self.s))
        self.s.run(3);resumed.run(3)
        self.assertEqual(self.s.days,resumed.days)
        self.assertEqual(dict(self.s.host.book.energy),dict(resumed.host.book.energy))
        self.assertEqual(dict(self.s.host.book.mass),dict(resumed.host.book.mass))
        self.assertEqual(self.s.bridge.phenotypes,resumed.bridge.phenotypes)
        self.assertEqual(self.s.bridge.tree.state,resumed.bridge.tree.state)
        self.book.audit();resumed.host.book.audit()

if __name__=='__main__':unittest.main()
