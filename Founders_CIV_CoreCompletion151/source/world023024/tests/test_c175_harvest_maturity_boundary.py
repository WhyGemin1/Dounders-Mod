"""C175: Founder harvest must independently reject premature mature-fruit checkpoint."""
import unittest
from run_world_tree_pilot import bootstrap
from founders_civ.core.founder_harvesting import observed_lots, perform_harvest

class HarvestMaturityBoundaryTests(unittest.TestCase):
    def test_corrupt_mature_record_cannot_transfer_fruit_before_policy_tick(self):
        sim, _, tid = bootstrap(seed=821)
        tree = sim.world_trees.worlds[tid]
        tree.enable_provisioning()
        for _ in range(17):
            sim.step()
        sim.founder_harvest_enabled = True
        founder = 'F001'
        sim.founders.people[founder].location = 'riverbank'
        tree.observe(founder)
        tree.observations[founder]['known_lots'] = observed_lots(tree)
        lot = next(x['lot'] for x in tree.observations[founder]['known_lots']
                   if x['kind'] == 'fruit')
        record = tree.provisioning.lots[lot]
        self.assertEqual(record.state, 'mature')
        record.created = tree.age  # corrupt restored chronology after observation
        before = (sim.book.seq, dict(sim.book.mass), dict(sim.book.energy),
                  dict(sim.book.operations))
        with self.assertRaisesRegex(ValueError, 'no longer available'):
            perform_harvest(sim, founder, (tid, lot, 'fruit'))
        self.assertEqual(before, (sim.book.seq, dict(sim.book.mass),
                                 dict(sim.book.energy), dict(sim.book.operations)))
        self.assertFalse(any(x['lot'] == lot for x in
                             tree.observations[founder]['known_lots']))
        sim.book.audit()

if __name__ == '__main__':
    unittest.main()
