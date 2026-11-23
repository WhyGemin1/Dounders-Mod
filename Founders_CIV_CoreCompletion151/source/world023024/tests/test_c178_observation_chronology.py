"""C178: observation must not propose checkpoint-corrupt Tree food or fruit."""
import unittest
from run_world_tree_pilot import bootstrap
from founders_civ.core.founder_harvesting import observed_lots


class ObservationChronologyTests(unittest.TestCase):
    def test_invalid_lot_chronology_is_not_advertised(self):
        for corruption in ('food_mature', 'food_future', 'food_boolean',
                           'fruit_premature', 'fruit_future'):
            with self.subTest(corruption=corruption):
                sim, _, tid = bootstrap(seed=821)
                tree = sim.world_trees.worlds[tid]
                tree.enable_provisioning()
                for _ in range(9):
                    sim.step()
                initial = observed_lots(tree)
                kind = 'fruit' if corruption.startswith('fruit') else 'food'
                entries = [x for x in initial if x['kind'] == kind]
                self.assertTrue(entries, 'fixture requires an observable lot')
                lot = entries[0]['lot']
                record = tree.provisioning.lots[lot]
                if corruption == 'food_mature':
                    record.state = 'mature'
                elif corruption == 'food_future':
                    record.created = tree.age + 1
                elif corruption == 'food_boolean':
                    record.created = True
                elif corruption == 'fruit_premature':
                    record.created = tree.age
                else:
                    record.created = tree.age + 1
                before = (sim.book.seq, dict(sim.book.mass),
                          dict(sim.book.energy), dict(sim.book.operations))
                self.assertNotIn(lot, [x['lot'] for x in observed_lots(tree)])
                self.assertEqual(before, (sim.book.seq, dict(sim.book.mass),
                                          dict(sim.book.energy), dict(sim.book.operations)))
                sim.book.audit()


if __name__ == '__main__':
    unittest.main()
