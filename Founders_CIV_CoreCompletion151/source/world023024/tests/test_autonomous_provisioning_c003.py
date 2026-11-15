"""U026-C003 offline tests of real two-Tree Book-funded provisioning.

No WorldBox live gameplay or native actor writes are executed.
"""
import copy
import pickle
import unittest
from run_world_tree_pilot import bootstrap


class AutonomousProvisioningTests(unittest.TestCase):
    def setUp(self):
        self.sim,self.realm,self.tid=bootstrap(seed=821)
        self.tree=self.sim.world_trees.worlds[self.tid]
        self.book=self.sim.book

    def advance(self,n):
        for _ in range(n):self.sim.step()

    def test_opt_in_preserves_control(self):
        self.advance(30)
        self.assertIsNone(self.tree.provisioning)
        self.assertFalse(any(x.startswith('fruit:C003-') for x in self.book.asset_ids))
        self.assertEqual(len(self.sim.founders.people),100)

    def test_autonomous_food_fruit_and_maturation(self):
        policy=self.tree.enable_provisioning()
        self.advance(20)
        self.assertTrue(any(e[0]=='grow' and '-food-' in e[1] for e in policy.events))
        self.assertTrue(any(e[0]=='grow' and '-fruit-' in e[1] for e in policy.events))
        self.assertTrue(policy.mature_fruit())
        self.assertLess(abs(self.book.audit()['energy_error']),1e-4)

    def test_reserve_first_low_plant_keeps_resources(self):
        policy=self.tree.enable_provisioning(minimum_plant=100.)
        pool=self.book.energy['river_pool']
        self.advance(40)
        self.assertEqual(policy.lots,{})
        self.assertAlmostEqual(pool,self.book.energy['river_pool'],delta=100.)  # natural world may spend river energy
        self.assertEqual(len(policy.events),0)

    def test_aged_lots_decay_and_recycle_ce(self):
        policy=self.tree.enable_provisioning()
        self.advance(38)
        aged=[(k,v) for k,v in policy.lots.items() if v.kind=='fruit' and v.created==12]
        self.assertEqual(len(aged),1)
        lot,record=aged[0]
        self.assertEqual(record.state,'decayed')
        self.assertAlmostEqual(self.book.mass[f'fruit:lot:{lot}:tree:{self.tid}'],0.)
        self.assertIn(f'fruit:{lot}',self.book.asset_ids)
        self.assertIn(f'fruit:decay:{self.tid}:{lot}',self.book.operations)
        self.assertLess(abs(self.book.audit()['mass_error']),1e-5)

    def test_mature_lot_harvest_founder_and_world_seed(self):
        policy=self.tree.enable_provisioning()
        self.advance(17)
        lot=policy.mature_fruit()[0]
        self.tree.resources.harvest_fruit(lot,'F001')
        self.assertAlmostEqual(self.book.energy[f'ce:fruit:lot:{lot}:founder:F001'],1.)
        self.tree.resources.fund_world_seed(lot,'F001','C003-SEED')
        self.assertAlmostEqual(self.book.mass['world_seed:C003-SEED'],.1)
        self.assertAlmostEqual(self.book.energy['ce:seed:C003-SEED'],1.)
        self.advance(35)
        self.assertEqual(policy.lots[lot].state,'transferred')
        self.assertLess(abs(self.book.audit()['mass_error']),1e-5)

    def test_tree_collapse_preserves_stored_fruit(self):
        policy=self.tree.enable_provisioning()
        self.advance(17)
        lot=policy.mature_fruit()[0]
        self.tree.collapse('test')
        self.assertEqual(self.tree.state,'archived')
        self.tree.resources.harvest_fruit(lot,'F001')
        self.assertAlmostEqual(self.book.mass[f'fruit:lot:{lot}:founder:F001'],.1)
        self.assertLess(abs(self.book.audit()['mass_error']),1e-5)

    def test_tick_replay_does_not_duplicate_events_or_assets(self):
        policy=self.tree.enable_provisioning()
        self.advance(24)
        before=(self.book.seq,len(self.book.asset_ids),len(policy.events))
        self.assertFalse(policy.tick())
        self.assertEqual(before,(self.book.seq,len(self.book.asset_ids),len(policy.events)))

    def test_pickle_checkpoint_replays_exactly(self):
        policy=self.tree.enable_provisioning()
        self.advance(21)
        resumed=pickle.loads(pickle.dumps(self.sim))
        for _ in range(15):
            self.sim.step();resumed.step()
        a=self.sim.world_trees.worlds[self.tid]
        b=resumed.world_trees.worlds[self.tid]
        self.assertEqual(a.provisioning.lots,b.provisioning.lots)
        self.assertEqual(a.provisioning.events,b.provisioning.events)
        self.assertEqual(dict(self.sim.book.mass),dict(resumed.book.mass))
        self.assertEqual(dict(self.sim.book.energy),dict(resumed.book.energy))
        self.assertEqual(self.sim.book.seq,resumed.book.seq)

    def test_finite_ce_blocks_fruit_without_minting(self):
        amount=self.book.energy['river_pool']
        self.book.move(energy=[('river_pool','environment:heat',amount)])
        policy=self.tree.enable_provisioning()
        self.advance(24)
        self.assertFalse(any(v.kind=='fruit' for v in policy.lots.values()))
        self.assertTrue(any(v.kind=='food' for v in policy.lots.values()))
        self.assertAlmostEqual(self.book.energy['ce:river'],0.)
        self.assertLess(abs(self.book.audit()['energy_error']),1e-4)

    def test_decay_atomic_and_idempotent(self):
        self.book.reserve_creation_charge(1.,'C003:reserve')
        self.tree.grow_creation_fruit('forest','C003-MANUAL')
        orig=self.tree.resources.decay_fruit('forest','C003-MANUAL')
        seq=self.book.seq
        self.assertEqual(self.tree.resources.decay_fruit('forest','C003-MANUAL'),orig)
        self.assertEqual(self.book.seq,seq)
        self.assertAlmostEqual(self.book.energy['ce:river'],1.)
        self.tree.make_portable_food('forest','C003-FOOD')
        food=self.tree.resources.decay_food('forest','C003-FOOD')
        seq=self.book.seq
        self.assertEqual(self.tree.resources.decay_food('forest','C003-FOOD'),food)
        self.assertEqual(self.book.seq,seq)

    def test_cannot_decay_a_harvested_fruit(self):
        self.book.reserve_creation_charge(1.,'C003:reserve')
        self.tree.grow_creation_fruit('forest','C003-MANUAL')
        self.tree.resources.harvest_fruit('C003-MANUAL','F001')
        seq=self.book.seq
        with self.assertRaises(ValueError):self.tree.resources.decay_fruit('forest','C003-MANUAL')
        self.assertEqual(self.book.seq,seq)

    def test_two_actual_trees_compete_for_one_river_charge(self):
        rs=self.sim.seeds
        founder=max(self.sim.founders.people,key=lambda a:(self.book.energy[f'founder:{a}'],a))
        world_bp=rs.draft(founder,'world','Second Living Tree',self.realm,x=69,y=44)
        rs.research(founder,world_bp.id)
        self.sim.step()
        if self.sim.tick not in world_bp.research_ticks:rs.research(founder,world_bp.id)
        reviewer=next(a for a,v in self.sim.founders.people.items() if a!=founder and v.location==self.sim.founders.people[founder].location)
        rs.validate(reviewer,world_bp.id)
        world=rs.plant(founder,world_bp.id)
        other=self.sim.world_trees.worlds[world['id']]
        founder=max(self.sim.founders.people,key=lambda a:(self.book.energy[f'founder:{a}'],a))
        sp=rs.draft(founder,'species','Second Grazers',other.id,x=69.3,y=44.1)
        rs.research(founder,sp.id)
        self.sim.step()
        if self.sim.tick not in sp.research_ticks:rs.research(founder,sp.id)
        reviewer=next(a for a,v in self.sim.founders.people.items() if a!=founder and v.location==self.sim.founders.people[founder].location)
        rs.validate(reviewer,sp.id)
        rs.plant(founder,sp.id)
        self.assertEqual(other.state,'active')
        self.tree.enable_provisioning(food_period=999,fruit_period=1)
        other.enable_provisioning(food_period=999,fruit_period=1)
        available=self.book.energy['river_pool']
        self.book.move(energy=[('river_pool','environment:heat',available-1.)])
        # Invoke each real Tree's policy in deterministic registry order.
        self.tree.provisioning.tick()
        other.provisioning.tick()
        produced=sum(v.kind=='fruit' for t in (self.tree,other) for v in t.provisioning.lots.values())
        self.assertEqual(produced,1)
        self.assertAlmostEqual(self.book.energy['river_pool'],0.)
        self.assertAlmostEqual(self.book.energy['ce:river'],0.)
        self.assertLess(abs(self.book.audit()['energy_error']),1e-4)

if __name__=='__main__':unittest.main()
