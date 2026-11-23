"""C174: fail closed on premature mature-fruit checkpoint states."""
import copy
import unittest
from run_world_tree_pilot import bootstrap


class PrematureFruitCheckpointTests(unittest.TestCase):
    def test_mature_fruit_before_maturity_rejected_without_book_mutation(self):
        sim, realm, tid = bootstrap(seed=821)
        tree = sim.world_trees.worlds[tid]
        policy = tree.enable_provisioning(food_period=999, fruit_period=1,
                                          maturity_days=5)
        sim.step()
        sim.step()
        lot = next(k for k, rec in policy.lots.items() if rec.kind == 'fruit')
        record = policy.lots[lot]
        self.assertLess(tree.age - record.created, policy.maturity_days)
        record.state = 'mature'  # Corrupted/restored checkpoint, not legitimate growth.
        tree.age += 1
        book = sim.book
        before = (policy.last_age, copy.deepcopy(policy.lots), list(policy.events),
                  book.seq, dict(book.mass), dict(book.energy),
                  dict(book.operations))
        with self.assertRaisesRegex(ValueError, 'invalid Tree provisioned-lot checkpoint'):
            policy.tick()
        self.assertEqual(before, (policy.last_age, policy.lots, policy.events,
                                 book.seq, dict(book.mass), dict(book.energy),
                                 dict(book.operations)))
        record.state = 'stored'
        policy.tick()
        book.audit()


if __name__ == '__main__':
    unittest.main()
