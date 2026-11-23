"""C183: corrupt harvest registry/policy must fail closed at the transfer boundary."""
import unittest
from run_world_tree_pilot import bootstrap
from founders_civ.core.founder_harvesting import observed_lots, perform_harvest


class HarvestCorruptionC183(unittest.TestCase):
    def setUp(self):
        self.sim, _, self.tid = bootstrap(seed=821)
        self.tree = self.sim.world_trees.worlds[self.tid]
        self.tree.enable_provisioning()
        for _ in range(17):
            self.sim.step()
        self.sim.founder_harvest_enabled = True
        self.actor = 'F001'
        self.sim.founders.people[self.actor].location = 'riverbank'
        self.tree.observe(self.actor)
        self.tree.observations[self.actor]['known_lots'] = observed_lots(self.tree)
        self.fruit = next(x['lot'] for x in self.tree.observations[self.actor]['known_lots']
                          if x['kind'] == 'fruit')
        self.food = next(x['lot'] for x in self.tree.observations[self.actor]['known_lots']
                         if x['kind'] == 'food')

    def assert_rejected_without_book_change(self, target):
        before = (self.sim.book.seq, dict(self.sim.book.mass), dict(self.sim.book.energy))
        with self.assertRaises(ValueError):
            perform_harvest(self.sim, self.actor, target)
        self.assertEqual(before, (self.sim.book.seq, dict(self.sim.book.mass),
                                  dict(self.sim.book.energy)))

    def test_invalid_registry(self):
        original = self.tree.provisioning.lots
        for value in (None, [], 'corrupt'):
            self.tree.provisioning.lots = value
            self.assert_rejected_without_book_change((self.tid, self.food, 'food'))
        self.tree.provisioning.lots = original

    def test_invalid_fruit_maturity_policy(self):
        original = self.tree.provisioning.maturity_days
        for value in (None, True, -1, 2.5, '3'):
            self.tree.provisioning.maturity_days = value
            self.assert_rejected_without_book_change((self.tid, self.fruit, 'fruit'))
        self.tree.provisioning.maturity_days = original

    def test_corrupted_record(self):
        original = self.tree.provisioning.lots[self.food]
        for value in (None, 7, 'stored'):
            self.tree.provisioning.lots[self.food] = value
            self.assert_rejected_without_book_change((self.tid, self.food, 'food'))
        self.tree.provisioning.lots[self.food] = original


if __name__ == '__main__':
    unittest.main()
