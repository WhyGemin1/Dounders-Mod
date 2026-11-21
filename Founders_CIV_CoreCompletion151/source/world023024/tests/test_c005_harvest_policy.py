"""U026-C005 regression guards for the opt-in Book-backed harvesting policy.

Requires the complete Core151/WORLD024 source tree; this single file is not
a substitute for the missing C003/C004 integration files.
"""
import unittest
from run_world_tree_pilot import bootstrap
from founders_civ.core.founder_harvesting import observed_lots,propose_harvest,perform_harvest


class HarvestPolicyGuards(unittest.TestCase):
    def setUp(self):
        self.sim,_,self.tid=bootstrap(seed=821)
        self.tree=self.sim.world_trees.worlds[self.tid]
        self.tree.enable_provisioning()
        for _ in range(17): self.sim.step()
        self.actor='F001'
        self.sim.founders.people[self.actor].location='riverbank'
        self.tree.observe(self.actor)
        self.tree.observations[self.actor]['known_lots']=observed_lots(self.tree)

    def test_disabled_policy_cannot_transfer_book_assets(self):
        self.sim.founder_harvest_enabled=False
        lot=next(x['lot'] for x in observed_lots(self.tree) if x['kind']=='food')
        seq=self.sim.book.seq
        self.assertEqual(propose_harvest(self.sim,self.actor),[])
        with self.assertRaisesRegex(ValueError,'disabled'):
            perform_harvest(self.sim,self.actor,(self.tid,lot,'food'))
        self.assertEqual(self.sim.book.seq,seq)

    def test_knowledge_is_not_omniscience(self):
        self.sim.founder_harvest_enabled=True
        self.tree.observations[self.actor]['known_lots']=[]
        self.assertEqual(propose_harvest(self.sim,self.actor),[])
        lot=next(x['lot'] for x in observed_lots(self.tree) if x['kind']=='fruit')
        seq=self.sim.book.seq
        with self.assertRaisesRegex(ValueError,'recent observation'):
            perform_harvest(self.sim,self.actor,(self.tid,lot,'fruit'))
        self.assertEqual(self.sim.book.seq,seq)

    def test_stale_book_lot_is_rejected_without_second_transfer(self):
        self.sim.founder_harvest_enabled=True
        lot=next(x['lot'] for x in observed_lots(self.tree) if x['kind']=='fruit')
        self.tree.resources.harvest_fruit(lot,'F002')
        seq=self.sim.book.seq
        with self.assertRaisesRegex(ValueError,'no longer available'):
            perform_harvest(self.sim,self.actor,(self.tid,lot,'fruit'))
        self.assertEqual(self.sim.book.seq,seq)
        self.assertFalse(any(x['lot']==lot for x in self.tree.observations[self.actor]['known_lots']))

if __name__=='__main__': unittest.main()
