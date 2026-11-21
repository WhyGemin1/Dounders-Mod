"""U026-C004: Founder information and actual Book-funded Tree harvest actions."""
import copy
import pickle
import unittest
from run_world_tree_pilot import bootstrap
from founders_civ.core.founder_harvesting import (observed_lots,propose_harvest,perform_harvest)


class FounderHarvestC004Tests(unittest.TestCase):
    def setUp(self):
        self.sim,self.realm,self.tid=bootstrap(seed=821)
        self.tree=self.sim.world_trees.worlds[self.tid]
        self.tree.enable_provisioning()
        for _ in range(17):self.sim.step()
        self.sim.founder_harvest_enabled=True
        self.f='F001'
        self.sim.founders.people[self.f].location='riverbank'
        self.book=self.sim.book

    def perceive(self):
        # Do not pretend an unobserved Founder knows the Tree's current Book.
        self.sim._current_parent=None
        self.tree.observe(self.f)
        self.tree.observations[self.f]['known_lots']=observed_lots(self.tree)
        return self.tree.observations[self.f]

    def test_no_omniscient_harvest_before_observing(self):
        self.assertTrue(self.tree.provisioning.mature_fruit())
        self.assertEqual(propose_harvest(self.sim,self.f),[])
        lot=self.tree.provisioning.mature_fruit()[0]
        with self.assertRaisesRegex(ValueError,'recent observation'):
            perform_harvest(self.sim,self.f,(self.tid,lot,'fruit'))

    def test_snapshot_contains_only_actual_mature_available_lots(self):
        evidence=self.perceive()
        avail=evidence['known_lots']
        self.assertTrue(any(x['kind']=='fruit' for x in avail))
        self.assertTrue(any(x['kind']=='food' for x in avail))
        self.assertNotIn('future',str(avail))
        self.assertEqual(len(avail),len(observed_lots(self.tree)))
        self.assertTrue(propose_harvest(self.sim,self.f))

    def test_fruit_transfer_and_conservation_no_actor_action_toll(self):
        self.perceive()
        lot=next(x['lot'] for x in self.tree.observations[self.f]['known_lots'] if x['kind']=='fruit')
        founder_before=self.book.energy[f'founder:{self.f}']
        mass_before=self.book.mass[f'fruit:lot:{lot}:tree:{self.tid}']
        res=perform_harvest(self.sim,self.f,(self.tid,lot,'fruit'))
        self.assertGreater(res.seq,0)
        self.assertAlmostEqual(self.book.mass[f'fruit:lot:{lot}:founder:{self.f}'],mass_before)
        self.assertAlmostEqual(self.book.energy[f'founder:{self.f}'],founder_before)
        self.assertEqual(self.tree.provisioning.lots[lot].state,'transferred')
        self.assertLess(abs(self.book.audit()['energy_error']),1e-4)
        self.assertLess(abs(self.book.audit()['mass_error']),1e-5)
        with self.assertRaisesRegex(ValueError,'recent observation'):
            perform_harvest(self.sim,self.f,(self.tid,lot,'fruit'))

    def test_food_transfer_and_ingestion_remain_separate(self):
        self.perceive()
        lot=next(x['lot'] for x in self.tree.observations[self.f]['known_lots'] if x['kind']=='food')
        old_gut=self.book.mass[f'gut:founder:{self.f}:lot:{lot}']
        perform_harvest(self.sim,self.f,(self.tid,lot,'food'))
        self.assertEqual(self.book.mass[f'gut:founder:{self.f}:lot:{lot}'],old_gut)
        self.tree.resources.eat_food(lot,self.f)
        self.assertGreater(self.book.mass[f'gut:founder:{self.f}:lot:{lot}'],old_gut)

    def test_rejects_remote_forged_or_stale_harvest(self):
        self.perceive()
        lot=next(x['lot'] for x in self.tree.observations[self.f]['known_lots'] if x['kind']=='fruit')
        orig_seq=self.book.seq
        self.sim.founders.people[self.f].location='house'
        with self.assertRaisesRegex(ValueError,'riverbank'):
            perform_harvest(self.sim,self.f,(self.tid,lot,'fruit'))
        self.sim.founders.people[self.f].location='riverbank'
        with self.assertRaisesRegex(ValueError,'recent observation'):
            perform_harvest(self.sim,self.f,(self.tid,'FORGED','fruit'))
        self.tree.observations[self.f]['seen_tick']=-100
        with self.assertRaisesRegex(ValueError,'recent observation'):
            perform_harvest(self.sim,self.f,(self.tid,lot,'fruit'))
        self.assertEqual(self.book.seq,orig_seq)

    def test_replay_one_lot_other_founder_cannot_steal(self):
        self.perceive()
        lot=next(x['lot'] for x in self.tree.observations[self.f]['known_lots'] if x['kind']=='fruit')
        self.sim.founders.people['F002'].location='riverbank'
        self.tree.observations['F002']=copy.deepcopy(self.tree.observations[self.f])
        perform_harvest(self.sim,self.f,(self.tid,lot,'fruit'))
        seq=self.book.seq
        with self.assertRaisesRegex(ValueError,'no longer available'):
            perform_harvest(self.sim,'F002',(self.tid,lot,'fruit'))
        self.assertFalse(any(x['lot']==lot for x in self.tree.observations['F002']['known_lots']))
        self.assertEqual(seq,self.book.seq)

    def test_checkpoint_restores_known_resources_and_idempotent_book(self):
        self.perceive()
        frozen=pickle.loads(pickle.dumps(self.sim))
        for sim in (self.sim,frozen):
            tree=sim.world_trees.worlds[self.tid]
            lot=next(x['lot'] for x in tree.observations[self.f]['known_lots'] if x['kind']=='fruit')
            perform_harvest(sim,self.f,(self.tid,lot,'fruit'))
        self.assertEqual(dict(self.sim.book.mass),dict(frozen.book.mass))
        self.assertEqual(dict(self.sim.book.energy),dict(frozen.book.energy))
        self.assertEqual(self.sim.book.seq,frozen.book.seq)

    def test_autonomous_proposal_and_do_stay_linked(self):
        self.perceive()
        self.sim.founder_harvest_enabled=True
        self.assertTrue(any(x[1]=='tree_harvest' for x in self.sim._proposals(self.f,[])))
        options=propose_harvest(self.sim,self.f)
        choice=next(x for x in options if x[3][2]=='fruit')
        eid=self.sim.log('test_decision',self.f,chosen='tree_harvest')
        old=self.book.seq
        self.sim._do(self.f,choice,[],None,eid)
        self.assertGreater(self.book.seq,old)
        self.assertTrue(any(e['action']=='tree_founder_harvest' for e in self.sim.events))
        self.assertFalse(any(x[3]==choice[3] for x in propose_harvest(self.sim,self.f)))  # Founder knows it was picked up

    def test_disabled_policy_rejects_direct_harvest(self):
        self.perceive()
        lot=next(x['lot'] for x in self.tree.observations[self.f]['known_lots'] if x['kind']=='fruit')
        self.sim.founder_harvest_enabled=False
        before=self.book.seq
        self.assertEqual(propose_harvest(self.sim,self.f),[])
        with self.assertRaisesRegex(ValueError,'disabled'):
            perform_harvest(self.sim,self.f,(self.tid,lot,'fruit'))
        self.assertEqual(self.book.seq,before)

    def test_disabled_provisioning_never_offers_resources(self):
        sim,realm,tid=bootstrap(seed=821)
        actor=next(a for a in sim.founders.people if sim.world_trees.worlds[tid].owner==a)
        sim.founders.people[actor].location='riverbank'
        sim.world_trees.worlds[tid].observe(actor)
        self.assertEqual(propose_harvest(sim,actor),[])


    def test_unripe_fruit_not_perceived_or_harvested(self):
        sim,realm,tid=bootstrap(seed=821)
        tree=sim.world_trees.worlds[tid];tree.enable_provisioning()
        for _ in range(12):sim.step()
        sim.founder_harvest_enabled=True
        actor='F001';sim.founders.people[actor].location='riverbank'
        tree.observe(actor)
        tree.observations[actor]['known_lots']=observed_lots(tree)
        self.assertFalse(any(x['kind']=='fruit' for x in tree.observations[actor]['known_lots']))
        lot=next(k for k,v in tree.provisioning.lots.items() if v.kind=='fruit')
        with self.assertRaisesRegex(ValueError,'recent observation'):
            perform_harvest(sim,actor,(tid,lot,'fruit'))

    def test_remnant_fruit_can_be_taken_after_tree_collapse(self):
        self.perceive()
        lot=next(x['lot'] for x in self.tree.observations[self.f]['known_lots'] if x['kind']=='fruit')
        self.tree.collapse('experimental collapse')
        perform_harvest(self.sim,self.f,(self.tid,lot,'fruit'))
        self.assertAlmostEqual(self.book.mass[f'fruit:lot:{lot}:founder:{self.f}'],.10)

    def test_manual_book_harvest_does_not_trap_founder_in_stale_claim(self):
        self.perceive()
        lot=next(x['lot'] for x in self.tree.observations[self.f]['known_lots'] if x['kind']=='fruit')
        self.tree.resources.harvest_fruit(lot,'F002')
        old=self.book.seq
        with self.assertRaisesRegex(ValueError,'no longer available'):
            perform_harvest(self.sim,self.f,(self.tid,lot,'fruit'))
        self.assertFalse(any(x['lot']==lot for x in self.tree.observations[self.f]['known_lots']))
        self.assertEqual(self.book.seq,old)

    def test_malformed_target_fails_without_book_mutation(self):
        self.perceive()
        old=self.book.seq
        for value in (None,(),('bad',),('a','b','not-food')):
            with self.assertRaises(ValueError):perform_harvest(self.sim,self.f,value)
        self.assertEqual(self.book.seq,old)

if __name__=='__main__':unittest.main()
