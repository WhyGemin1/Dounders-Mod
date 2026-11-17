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

    def test_collapsed_tree_remnants_still_mature_without_new_growth(self):
        policy=self.tree.enable_provisioning(food_period=999,fruit_period=1)
        self.advance(2)
        stored=[lot for lot,rec in policy.lots.items()
                if rec.kind=='fruit' and rec.state=='stored']
        self.assertTrue(stored)
        lot=stored[0]
        self.tree.collapse('remnant-aging-test')
        produced=len(policy.lots)
        self.tree.age+=policy.maturity_days
        policy.tick()
        self.assertEqual(policy.lots[lot].state,'mature')
        self.assertEqual(len(policy.lots),produced)
        self.assertGreater(self.book.mass[f'fruit:lot:{lot}:tree:{self.tid}'],0.)
        self.book.audit()
        # Replaying the same age must not duplicate maturation events.
        before=(self.book.seq,list(policy.events))
        self.assertFalse(policy.tick())
        self.assertEqual((self.book.seq,policy.events),before)

    def test_archived_tree_without_provisioning_still_ages(self):
        # C026: elapsed world time must not depend on optional food policy.
        self.assertIsNone(self.tree.provisioning)
        self.advance(2)
        self.tree.collapse('unprovisioned-remnant-clock')
        age=self.tree.age
        founder_ids=set(self.sim.founders.people)
        book_seq=self.book.seq
        self.advance(7)
        self.assertEqual(self.tree.age,age+7)
        self.assertIsNone(self.tree.provisioning)
        self.assertEqual(set(self.sim.founders.people),founder_ids)
        self.assertGreaterEqual(self.book.seq,book_seq)
        self.book.audit()

    def test_archived_remnants_age_under_global_scheduler(self):
        policy=self.tree.enable_provisioning(food_period=999,fruit_period=1)
        self.advance(2)
        stored=[lot for lot,rec in policy.lots.items()
                if rec.kind=='fruit' and rec.state=='stored']
        self.assertTrue(stored)
        lot=stored[0]
        self.tree.collapse('scheduled-remnant-test')
        count=len(policy.lots)
        age=self.tree.age
        self.advance(policy.maturity_days)
        self.assertEqual(self.tree.age,age+policy.maturity_days)
        self.assertEqual(policy.lots[lot].state,'mature')
        self.assertEqual(len(policy.lots),count)
        self.assertEqual(len(self.sim.founders.people),100)
        self.assertLess(abs(self.book.audit()['mass_error']),1e-5)
        snapshot=(self.book.seq,list(policy.events))
        self.assertFalse(policy.tick())
        self.assertEqual((self.book.seq,policy.events),snapshot)

    def test_invalid_habitat_rotation_rejects_before_book_mutation(self):
        # C033: corrupt scheduler habitat inputs must fail closed.
        policy=self.tree.enable_provisioning(food_period=1,fruit_period=1)
        self.advance(2)
        self.tree.age+=1
        before=(policy.last_age,copy.deepcopy(policy.lots),list(policy.events),
                dict(self.book.mass),dict(self.book.energy),self.book.seq)
        original=self.tree.habitats
        self.tree.habitats=()
        try:
            with self.assertRaisesRegex(ValueError,'invalid Tree habitat'):
                policy.tick()
        finally:
            self.tree.habitats=original
        self.assertEqual(before,(policy.last_age,policy.lots,policy.events,
                                 dict(self.book.mass),dict(self.book.energy),self.book.seq))
        policy.tick()
        self.book.audit()

    def test_detached_book_rejects_provisioning_without_side_effects(self):
        # C027: production must never use an unregistered second Book.
        policy=self.tree.enable_provisioning(food_period=1,fruit_period=1)
        self.advance(2)
        before=(policy.last_age,copy.deepcopy(policy.lots),list(policy.events),
                dict(self.book.mass),dict(self.book.energy),self.book.seq)
        authoritative=self.tree.book
        self.tree.book=object()
        try:
            with self.assertRaisesRegex(ValueError,'authoritative simulation Book'):
                policy.tick()
        finally:
            self.tree.book=authoritative
        after=(policy.last_age,policy.lots,policy.events,
               dict(self.book.mass),dict(self.book.energy),self.book.seq)
        self.assertEqual(before,after)
        self.book.audit()

    def test_invalid_world_namespace_rejects_before_remnant_refresh(self):
        # C028: a malformed World ID must not age lots or mutate the Book,
        # even on an archived Tree that cannot produce new food or fruit.
        policy=self.tree.enable_provisioning(food_period=999,fruit_period=1)
        self.advance(2)
        self.tree.collapse('invalid-world-id-check')
        self.tree.age+=policy.maturity_days
        before=(policy.last_age,copy.deepcopy(policy.lots),list(policy.events),
                dict(self.book.mass),dict(self.book.energy),self.book.seq)
        self.tree.world_id='bad:namespace'
        try:
            with self.assertRaisesRegex(ValueError,'invalid World identity'):
                policy.tick()
        finally:
            del self.tree.world_id
        after=(policy.last_age,policy.lots,policy.events,
               dict(self.book.mass),dict(self.book.energy),self.book.seq)
        self.assertEqual(before,after)
        policy.tick()
        self.assertTrue(any(rec.state=='mature' for rec in policy.lots.values()))
        self.book.audit()

    def test_world_reassignment_rejected_after_lot_issuance(self):
        # C029: checkpoint ownership cannot silently switch Worlds once
        # physical lots exist, even after collapse.
        self.tree.world_id='WORLD-A'
        policy=self.tree.enable_provisioning(food_period=999,fruit_period=1)
        self.advance(2)
        self.assertTrue(policy.lots)
        self.tree.collapse('namespace-stability-test')
        self.tree.age+=policy.maturity_days
        before=(policy.last_age,copy.deepcopy(policy.lots),list(policy.events),
                dict(self.book.mass),dict(self.book.energy),self.book.seq)
        self.tree.world_id='WORLD-B'
        with self.assertRaisesRegex(ValueError,'World identity changed'):
            policy.tick()
        self.assertEqual(before,(policy.last_age,policy.lots,policy.events,
                                 dict(self.book.mass),dict(self.book.energy),self.book.seq))
        self.tree.world_id='WORLD-A'
        policy.tick()
        self.assertTrue(any(v.state=='mature' for v in policy.lots.values()))
        self.book.audit()

    def test_foreign_tree_lot_rejected_before_remnant_aging(self):
        # C030: a lot from another Tree in the same World must not be
        # accepted solely because its World namespace matches.
        from founders_civ.core.autonomous_provisioning import ProvisionedLot
        self.tree.world_id='WORLD-A'
        policy=self.tree.enable_provisioning(food_period=999,fruit_period=1)
        self.advance(2)
        self.tree.collapse('foreign-tree-lot')
        self.tree.age+=policy.maturity_days
        original=next(iter(policy.lots))
        record=policy.lots.pop(original)
        foreign=f'W-WORLD-A-C003-FOREIGN-TREE-fruit-{record.created}'
        policy.lots[foreign]=record
        before=(policy.last_age,copy.deepcopy(policy.lots),list(policy.events),
                dict(self.book.mass),dict(self.book.energy),self.book.seq)
        with self.assertRaisesRegex(ValueError,'World identity changed'):
            policy.tick()
        self.assertEqual(before,(policy.last_age,policy.lots,policy.events,
                                 dict(self.book.mass),dict(self.book.energy),self.book.seq))
        policy.lots.pop(foreign)
        policy.lots[original]=record
        policy.tick()
        self.assertEqual(policy.lots[original].state,'mature')
        self.book.audit()

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

    def test_g1_failed_fruit_growth_rolls_back_reserved_ce(self):
        # Inject a failure between river CE reservation and fruit creation.
        # A rejected composite operation must leave the Book unchanged.
        from unittest.mock import patch
        policy=self.tree.enable_provisioning(minimum_plant=0.)
        biome=next(p for p in self.tree.habitats
                   if policy._reserve(p,.10,False))
        self.assertLess(self.book.energy['ce:river'],1.)
        self.assertGreaterEqual(self.book.energy['river_pool'],1.)
        before=(dict(self.book.mass),dict(self.book.energy),self.book.seq,
                dict(self.book.operations),set(self.book.asset_ids))
        with patch.object(self.tree,'grow_creation_fruit',
                          side_effect=RuntimeError('injected fruit failure')):
            with self.assertRaisesRegex(RuntimeError,'injected fruit failure'):
                policy._allocate('fruit',biome)
        self.assertEqual(before,(dict(self.book.mass),dict(self.book.energy),
                                 self.book.seq,dict(self.book.operations),
                                 set(self.book.asset_ids)))
        self.assertEqual(policy.lots,{})
        self.book.audit()

    def test_g1_failed_world_plant_rolls_back_book_and_registry(self):
        # Fail after construct build and Tree registration but before the
        # success event: no planted Tree or spent Book resources may survive.
        from unittest.mock import patch
        rs=self.sim.seeds
        founder=max(self.sim.founders.people,
                    key=lambda a:(self.book.energy[f'founder:{a}'],a))
        bp=rs.draft(founder,'world','G1 Atomicity Tree',self.realm,x=69,y=44)
        rs.research(founder,bp.id)
        self.sim.step()
        if self.sim.tick not in bp.research_ticks:rs.research(founder,bp.id)
        reviewer=next(a for a,v in self.sim.founders.people.items()
                      if a!=founder and v.location==self.sim.founders.people[founder].location)
        rs.validate(reviewer,bp.id)
        before=(dict(self.book.mass),dict(self.book.energy),self.book.seq,
                dict(self.book.operations),set(self.book.asset_ids),
                set(rs.plants),set(rs.constructs.items),
                set(self.sim.world_trees.worlds),bp.stage,bp.planted_id,
                len(self.sim.events),len(rs.constructs.events))
        with patch.object(rs,'_event',side_effect=RuntimeError('injected plant finalization')):
            with self.assertRaisesRegex(RuntimeError,'injected plant finalization'):
                rs.plant(founder,bp.id)
        after=(dict(self.book.mass),dict(self.book.energy),self.book.seq,
               dict(self.book.operations),set(self.book.asset_ids),
               set(rs.plants),set(rs.constructs.items),
               set(self.sim.world_trees.worlds),bp.stage,bp.planted_id,
               len(self.sim.events),len(rs.constructs.events))
        self.assertEqual(before,after)
        self.book.audit()

    def test_g1_failed_species_plant_restores_existing_tree(self):
        # The Species Seed introduces residents to an existing Tree. Inject
        # a failure after those residents are created and verify that their
        # Book mass/fuel, IDs, membership and events all roll back together.
        from unittest.mock import patch
        rs=self.sim.seeds
        founder=max(self.sim.founders.people,
                    key=lambda a:(self.book.energy[f'founder:{a}'],a))
        wb=rs.draft(founder,'world','G1 Species Rollback Tree',self.realm,x=69,y=44)
        rs.research(founder,wb.id)
        self.sim.step()
        if self.sim.tick not in wb.research_ticks:rs.research(founder,wb.id)
        reviewer=next(a for a,v in self.sim.founders.people.items()
                      if a!=founder and v.location==self.sim.founders.people[founder].location)
        rs.validate(reviewer,wb.id)
        new_world=rs.plant(founder,wb.id)
        tid=new_world['id']
        tree=self.sim.world_trees.worlds[tid]
        founder=max(self.sim.founders.people,
                    key=lambda a:(self.book.energy[f'founder:{a}'],a))
        sb=rs.draft(founder,'species','G1 Interrupted Species',tid,x=69.3,y=44.1)
        rs.research(founder,sb.id)
        self.sim.step()
        if self.sim.tick not in sb.research_ticks:rs.research(founder,sb.id)
        reviewer=next(a for a,v in self.sim.founders.people.items()
                      if a!=founder and v.location==self.sim.founders.people[founder].location)
        rs.validate(reviewer,sb.id)
        before=(dict(self.book.mass),dict(self.book.energy),self.book.seq,
                len(tree.residents),tree.serial,tuple(tree.species_seed_ids),
                set(rs.constructs.items[tid].inhabitants),
                rs.plants[tid]['inhabitants'],len(self.sim.events),
                len(tree.timeline),sb.stage,sb.planted_id)
        with patch.object(rs,'_event',side_effect=RuntimeError('injected species finalization')):
            with self.assertRaisesRegex(RuntimeError,'injected species finalization'):
                rs.plant(founder,sb.id)
        after=(dict(self.book.mass),dict(self.book.energy),self.book.seq,
               len(tree.residents),tree.serial,tuple(tree.species_seed_ids),
               set(rs.constructs.items[tid].inhabitants),
               rs.plants[tid]['inhabitants'],len(self.sim.events),
               len(tree.timeline),sb.stage,sb.planted_id)
        self.assertEqual(before,after)
        self.book.audit()

    def test_g1_failed_tree_maintenance_rolls_back_founder_fuel(self):
        from unittest.mock import patch
        rs=self.sim.seeds
        actor=max(self.sim.founders.people,
                  key=lambda a:(self.book.energy[f'founder:{a}'],a))
        self.assertGreater(self.book.energy[f'founder:{actor}'],.1)
        before=(dict(self.book.mass),dict(self.book.energy),self.book.seq,
                copy.deepcopy(rs.owner_reserve_knowledge),
                len(rs.constructs.events),len(self.sim.events),self.sim.next_event)
        with patch.object(self.sim,'log',side_effect=RuntimeError('injected upkeep log')):
            with self.assertRaisesRegex(RuntimeError,'injected upkeep log'):
                rs.tend(actor,self.tid,.1)
        after=(dict(self.book.mass),dict(self.book.energy),self.book.seq,
               copy.deepcopy(rs.owner_reserve_knowledge),
               len(rs.constructs.events),len(self.sim.events),self.sim.next_event)
        self.assertEqual(before,after)
        self.book.audit()

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
