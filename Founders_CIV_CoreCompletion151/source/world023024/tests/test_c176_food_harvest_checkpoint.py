"""C176: a corrupt food checkpoint cannot authorize Founder harvest."""
import unittest
from run_world_tree_pilot import bootstrap
from founders_civ.core.founder_harvesting import observed_lots, perform_harvest


class FoodHarvestCheckpointTests(unittest.TestCase):
    def test_invalid_food_states_and_chronology_reject_without_book_transfer(self):
        for corruption in ('mature', 'future', 'boolean', 'negative'):
            with self.subTest(corruption=corruption):
                sim, _, tid = bootstrap(seed=821)
                tree = sim.world_trees.worlds[tid]
                tree.enable_provisioning()
                for _ in range(9):
                    sim.step()
                sim.founder_harvest_enabled = True
                founder = 'F001'
                sim.founders.people[founder].location = 'riverbank'
                tree.observe(founder)
                tree.observations[founder]['known_lots'] = observed_lots(tree)
                lot = next(x['lot'] for x in tree.observations[founder]['known_lots']
                           if x['kind'] == 'food')
                record = tree.provisioning.lots[lot]
                if corruption == 'mature':
                    record.state = 'mature'
                elif corruption == 'future':
                    record.created = tree.age + 1
                elif corruption == 'boolean':
                    record.created = True
                else:
                    record.created = -1
                before = (sim.book.seq, dict(sim.book.mass),
                          dict(sim.book.energy), dict(sim.book.operations))
                with self.assertRaisesRegex(ValueError, 'no longer available'):
                    perform_harvest(sim, founder, (tid, lot, 'food'))
                self.assertEqual(before, (sim.book.seq, dict(sim.book.mass),
                                          dict(sim.book.energy),
                                          dict(sim.book.operations)))
                sim.book.audit()


if __name__ == '__main__':
    unittest.main()
