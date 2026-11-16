"""U026 C002 tests: real Core151 Book and real WORLD-024 World Tree."""
import copy
import unittest

from founders_civ.core.ledger import Book
from run_world_tree_pilot import bootstrap


class BookIdentityTests(unittest.TestCase):
    def setUp(self):
        self.b=Book()
        self.b.seed_mass('plant:patch',2)
        self.b.seed_energy('house',10)
        self.b.seed_energy('river_pool',5)
        self.b.seed_energy('world_toll',0)
        self.b.seed_energy('underworld:0',0)
        self.b.freeze()

    def test_reserve_charge_conserved_and_replay(self):
        start=self.b.audit()['energy_total']
        t=self.b.reserve_creation_charge(2,'river:01')
        seq=self.b.seq
        self.assertEqual(t,self.b.reserve_creation_charge(2,'river:01'))
        self.assertEqual(self.b.seq,seq)
        self.assertEqual(self.b.energy['ce:river'],2)
        self.assertEqual(self.b.energy['river_pool'],3)
        self.assertAlmostEqual(start,self.b.audit()['energy_total'])

    def test_duplicate_operation_conflict_fail_closed(self):
        self.b.reserve_creation_charge(2,'river:01')
        before=dict(self.b.energy)
        with self.assertRaisesRegex(ValueError,'conflicting'):
            self.b.reserve_creation_charge(3,'river:01')
        self.assertEqual(dict(self.b.energy),before)

    def test_charge_overdraw_no_effect(self):
        before=dict(self.b.energy)
        with self.assertRaisesRegex(ValueError,'overdraw'):
            self.b.reserve_creation_charge(99,'river:too-much')
        self.assertEqual(dict(self.b.energy),before)
        self.assertEqual(self.b.operations,{})

    def test_charge_cannot_become_metabolism_or_heat(self):
        self.b.reserve_creation_charge(2,'river:01')
        before=dict(self.b.energy)
        for dst in ('house','metabolic:bear','environment:heat'):
            with self.subTest(dst=dst),self.assertRaisesRegex(ValueError,'mismatch'):
                self.b.move(energy=[('ce:river',dst,.1)])
        self.assertEqual(dict(self.b.energy),before)

    def test_generic_energy_cannot_become_charge(self):
        with self.assertRaisesRegex(ValueError,'mismatch'):
            self.b.move(energy=[('house','ce:river',.5)])

    def test_ce_cannot_supply_work(self):
        self.b.reserve_creation_charge(2,'river:01')
        with self.assertRaisesRegex(ValueError,'cannot be used'):
            self.b.transform([('plant:patch','seed:test',.1)],'ce:river',.1,
                energy_outputs=[('ce:river','ce:seed:test',.09)])

    def test_forever_unique_asset_id(self):
        tx=self.b.transform([('plant:patch','portable_food:lot:A:tree:X',.10)],
                source='river_pool',work=.01,
                energy_outputs=[('river_pool','heat:patch',.009)],
                operation_id='make:A',asset_id='food:A')
        self.b.move(material=[('portable_food:lot:A:tree:X','portable_food:lot:A:founder:F001',.1)])
        with self.assertRaisesRegex(ValueError,'duplicate permanent asset'):
            self.b.transform([('plant:patch','portable_food:lot:A:tree:X',.10)],
                    source='river_pool',work=.01,
                    energy_outputs=[('river_pool','heat:patch',.009)],
                    operation_id='make:B',asset_id='food:A')
        self.assertEqual(self.b.operations['make:A'][1],tx)

    def test_idempotence_survives_deepcopy_checkpoint(self):
        self.b.reserve_creation_charge(2,'river:01')
        copybook=copy.deepcopy(self.b)
        self.assertEqual(copybook.reserve_creation_charge(2,'river:01').seq,1)
        self.assertEqual(copybook.seq,1)
        self.assertEqual(copybook.audit()['idempotent_operations'],1)

    def test_failed_transform_does_not_reserve_asset(self):
        with self.assertRaisesRegex(ValueError,'overdraw'):
            self.b.transform([('plant:patch','fruit:lot:X:tree:T',5)],'river_pool',.01,
                [('river_pool','heat:patch',.009)],operation_id='make:X',asset_id='fruit:X')
        self.assertNotIn('fruit:X',self.b.asset_ids)
        self.assertNotIn('make:X',self.b.operations)

    def test_portable_food_ingest_typed(self):
        b=self.b
        # Seed before freeze in a new empty Book to exercise paired nutrition.
        b=Book()
        b.seed_mass('portable_food:lot:L:founder:F001',.1)
        b.seed_energy('food_energy:lot:L:founder:F001',.2)
        b.freeze()
        tx=b.ingest(
            [('portable_food:lot:L:founder:F001','gut:founder:F001',.1)],
            [('food_energy:lot:L:founder:F001','gut_energy:founder:F001',.2)],
            operation_id='eat:L')
        self.assertEqual(b.ingest(tx.material,tx.energy,'eat:L'),tx)
        self.assertEqual(b.energy['gut_energy:founder:F001'],.2)
        self.assertEqual(b.mass['gut:founder:F001'],.1)
        self.assertAlmostEqual(b.audit()['mass_error'],0)


class RealWorldTreeTests(unittest.TestCase):
    def setUp(self):
        self.sim,self.realm,self.tid=bootstrap(seed=820)
        self.tree=self.sim.world_trees.worlds[self.tid]
        self.ops=self.tree.resources

    def test_real_tree_to_founder_to_funded_seed(self):
        b=self.sim.book
        r0=b.energy['river_pool']
        b.reserve_creation_charge(1,'reserve:001')
        fruit=self.tree.grow_creation_fruit('forest','C002-FR01')
        self.assertEqual(fruit.kind,'transform')
        self.assertEqual(b.energy['ce:river'],0)
        self.ops.harvest_fruit('C002-FR01','F001')
        seed=self.ops.fund_world_seed('C002-FR01','F001','C002-SEED01')
        self.assertEqual(seed.kind,'transform')
        self.assertEqual(b.mass['world_seed:C002-SEED01'],.1)
        self.assertEqual(b.energy['ce:seed:C002-SEED01'],1)
        self.assertLess(b.energy['river_pool'],r0)
        self.assertLess(abs(b.audit()['mass_error']),1e-6)
        self.assertLess(abs(b.audit()['energy_error']),1e-6)

    def test_fruit_river_is_finite_and_not_minted_per_tree(self):
        b=self.sim.book
        b.reserve_creation_charge(1,'reserve:001')
        self.tree.grow_creation_fruit('forest','FR1')
        before=dict(b.mass),dict(b.energy),b.seq
        with self.assertRaisesRegex(ValueError,'overdraw'):
            self.tree.grow_creation_fruit('forest','FR2')
        self.assertEqual((dict(b.mass),dict(b.energy),b.seq),before)

    def test_duplicate_harvest_and_seed_replay_are_safe(self):
        b=self.sim.book
        b.reserve_creation_charge(1,'reserve:001')
        growth=self.tree.grow_creation_fruit('forest','FR1')
        self.assertEqual(self.tree.grow_creation_fruit('forest','FR1'),growth)
        harvest=self.ops.harvest_fruit('FR1','F001')
        self.assertEqual(self.ops.harvest_fruit('FR1','F001'),harvest)
        seed=self.ops.fund_world_seed('FR1','F001','S1')
        self.assertEqual(self.ops.fund_world_seed('FR1','F001','S1'),seed)
        self.assertEqual(b.mass['world_seed:S1'],.1)
        self.assertEqual(len(b.asset_ids),2)

    def test_original_fruit_identity_cannot_remint(self):
        b=self.sim.book
        b.reserve_creation_charge(2,'reserve:001')
        self.tree.grow_creation_fruit('forest','FR1')
        self.ops.harvest_fruit('FR1','F001')
        with self.assertRaisesRegex(ValueError,'duplicate permanent asset'):
            b.transform([(self.tree.acct('plant','forest'),
                         f'fruit:lot:FR1:tree:{self.tid}',.1)],
                        self.tree.acct('sun','forest'),.01,
                        [(self.tree.acct('sun','forest'),self.tree.acct('heat','forest'),.9*.01),
                         ('ce:river',f'ce:fruit:lot:FR1:tree:{self.tid}',1)],
                        operation_id='fruit:grow:second_attempt',asset_id='fruit:FR1')

    def test_portable_food_survives_tree_collapse(self):
        b=self.sim.book
        self.tree.make_portable_food('forest','FOOD1')
        self.ops.harvest_food('FOOD1','F001')
        self.tree.collapse('test_drought')
        self.assertEqual(self.tree.state,'archived')
        self.assertAlmostEqual(b.mass['portable_food:lot:FOOD1:founder:F001'],.08)
        self.ops.eat_food('FOOD1','F001')
        self.assertAlmostEqual(b.mass['gut:founder:F001:lot:FOOD1'],.08)
        self.assertAlmostEqual(b.energy['gut_energy:founder:F001:lot:FOOD1'],.02)
        self.assertLess(abs(b.audit()['mass_error']),1e-6)

    def test_cannot_create_goods_from_dead_tree(self):
        self.tree.collapse('test')
        with self.assertRaisesRegex(ValueError,'inactive Tree'):
            self.tree.grow_creation_fruit('forest','FR1')
        with self.assertRaisesRegex(ValueError,'inactive Tree'):
            self.tree.make_portable_food('forest','FD1')

    def test_founder_cannot_spend_another_founders_fruit(self):
        b=self.sim.book
        b.reserve_creation_charge(1,'reserve:001')
        self.tree.grow_creation_fruit('forest','FR1')
        self.ops.harvest_fruit('FR1','F001')
        start=b.seq
        with self.assertRaisesRegex(ValueError,'overdraw'):
            self.ops.fund_world_seed('FR1','F002','S1')
        self.assertEqual(b.seq,start)
        self.assertNotIn('seed:S1',b.asset_ids)

    def test_bad_names_and_habitat_fail_before_book_mutation(self):
        b=self.sim.book
        seq=b.seq
        with self.assertRaises(ValueError):self.tree.make_portable_food('ocean','X')
        with self.assertRaises(ValueError):self.tree.grow_creation_fruit('forest','bad:account')
        with self.assertRaises(ValueError):self.ops.harvest_fruit('test','NOT-A-FOUNDER')
        self.assertEqual(seq,b.seq)

    def test_portable_food_not_instant_fuel(self):
        b=self.sim.book
        self.tree.make_portable_food('forest','FOOD1')
        self.ops.harvest_food('FOOD1','F001')
        founder_fuel=b.energy['founder:F001']
        self.ops.eat_food('FOOD1','F001')
        self.assertAlmostEqual(b.energy['founder:F001'],founder_fuel)



class C002HardeningTests(unittest.TestCase):
    def setUp(self):
        self.sim,self.realm,self.tid=bootstrap(seed=824)
        self.tree=self.sim.world_trees.worlds[self.tid]
        self.book=self.sim.book
        self.ops=self.tree.resources

    def test_fruit_cannot_be_split_between_founders(self):
        self.book.reserve_creation_charge(1,'reserve:split')
        self.tree.grow_creation_fruit('forest','FR-SPLIT')
        before=(self.book.seq,dict(self.book.mass),dict(self.book.energy))
        with self.assertRaisesRegex(ValueError,'transfer in full'):
            self.ops.harvest_fruit('FR-SPLIT','F001',biomass=.05,creation_charge=.5)
        self.assertEqual(before,(self.book.seq,dict(self.book.mass),dict(self.book.energy)))
        self.ops.harvest_fruit('FR-SPLIT','F001')
        with self.assertRaises(ValueError):
            self.ops.harvest_fruit('FR-SPLIT','F002')

    def test_food_cannot_be_split(self):
        self.tree.make_portable_food('forest','FOOD-SPLIT')
        before=self.book.seq
        with self.assertRaisesRegex(ValueError,'transfer in full'):
            self.ops.harvest_food('FOOD-SPLIT','F001',biomass=.04,chemical=.01)
        self.assertEqual(before,self.book.seq)
        self.ops.harvest_food('FOOD-SPLIT','F001')
        with self.assertRaisesRegex(ValueError,'transfer in full'):
            self.ops.eat_food('FOOD-SPLIT','F001',biomass=.04,chemical=.01)
        self.assertAlmostEqual(self.book.mass['gut:founder:F001'],0.)

    def test_replay_of_growth_after_collapse_is_safe(self):
        self.book.reserve_creation_charge(1,'reserve:collapse')
        original=self.tree.grow_creation_fruit('forest','FR-OLD')
        old_food=self.tree.make_portable_food('forest','FD-OLD')
        self.tree.collapse('test')
        before=self.book.seq
        self.assertEqual(self.tree.grow_creation_fruit('forest','FR-OLD'),original)
        self.assertEqual(self.tree.make_portable_food('forest','FD-OLD'),old_food)
        self.assertEqual(self.book.seq,before)
        with self.assertRaisesRegex(ValueError,'conflicting'):
            self.tree.grow_creation_fruit('forest','FR-OLD',biomass=.2)

    def test_bool_and_nonfinite_quantities_rejected(self):
        import math
        before=self.book.seq
        for value in (True,math.inf,math.nan,0,-1):
            with self.subTest(value=value),self.assertRaisesRegex(ValueError,'invalid'):
                self.tree.make_portable_food('forest','FD-BAD',biomass=value)
        self.assertEqual(self.book.seq,before)

    def test_seed_spend_uses_founder_not_river_for_shaping_work(self):
        self.book.reserve_creation_charge(1,'reserve:seed')
        self.tree.grow_creation_fruit('forest','FR-SEED')
        self.ops.harvest_fruit('FR-SEED','F001')
        before=self.book.energy['founder:F001']
        self.ops.fund_world_seed('FR-SEED','F001','SEED-ONE')
        self.assertAlmostEqual(self.book.energy['founder:F001'],before-.01)
        self.assertAlmostEqual(self.book.energy['ce:seed:SEED-ONE'],1.)
        self.assertLess(abs(self.book.audit()['energy_error']),1e-6)

    def test_checkpoint_pickle_preserves_idempotency(self):
        import pickle
        self.book.reserve_creation_charge(1,'reserve:checkpoint')
        original=self.tree.grow_creation_fruit('forest','FR-CP')
        restored=pickle.loads(pickle.dumps(self.book))
        replay=restored.transform(original.material,
            source=self.tree.acct('sun','forest'),work=.01,
            energy_outputs=[(self.tree.acct('sun','forest'),self.tree.acct('heat','forest'),.009),
                ('ce:river',f'ce:fruit:lot:FR-CP:tree:{self.tid}',1.0)],
            operation_id=f'fruit:grow:{self.tid}:FR-CP',asset_id='fruit:FR-CP')
        self.assertEqual(replay,original)
        self.assertEqual(restored.seq,self.book.seq)

    def test_fruit_production_consumes_shared_finite_ce(self):
        self.book.reserve_creation_charge(2,'reserve:all')
        self.tree.grow_creation_fruit('forest','FR-ONE')
        self.tree.grow_creation_fruit('grassland','FR-TWO')
        with self.assertRaisesRegex(ValueError,'overdraw'):
            self.tree.grow_creation_fruit('wetland','FR-THREE')
        self.assertAlmostEqual(self.book.energy['ce:river'],0)
        self.assertLess(abs(self.book.audit()['mass_error']),1e-6)

if __name__=='__main__':unittest.main()
