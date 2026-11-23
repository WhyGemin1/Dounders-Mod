"""C166: failed Tree allocation retains checkpoint age for deterministic retry."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from founders_civ.core.autonomous_provisioning import TreeProvisioningPolicy
from founders_civ.core.ledger import Book

class AllocationRetryTests(unittest.TestCase):
    def test_failed_fruit_allocation_retries_same_age(self):
        book = Book()
        tree = SimpleNamespace(
            book=book, sim=SimpleNamespace(book=book, seeds=SimpleNamespace(
                plants={'TREE-TEST': {'status': 'stable'}})),
            world_id=None, habitats=('river',), age=24,
            state='active', id='TREE-TEST')
        policy = TreeProvisioningPolicy(tree)
        calls = []
        def allocate(kind, biome):
            calls.append((kind, biome))
            if len(calls) == 2:
                raise ValueError('Book rejected fruit')
            return True
        with patch.object(policy, '_refresh'), patch.object(
                policy, '_allocate', side_effect=allocate):
            with self.assertRaisesRegex(ValueError, 'Book rejected fruit'):
                policy.tick()
            self.assertEqual(policy.last_age, -1)
            self.assertTrue(policy.tick())
            self.assertEqual(policy.last_age, 24)
            self.assertEqual(calls, [('food', 'river'), ('fruit', 'river'),
                                     ('food', 'river'), ('fruit', 'river')])
            self.assertFalse(policy.tick())
            self.assertEqual(len(calls), 4)

if __name__ == '__main__':
    unittest.main()
