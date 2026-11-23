"""C165: a failed physical lot refresh must not consume a scheduler age."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from founders_civ.core.autonomous_provisioning import TreeProvisioningPolicy
from founders_civ.core.ledger import Book


class RefreshRetryTests(unittest.TestCase):
    def test_failed_refresh_does_not_consume_age(self):
        book = Book()
        tree = SimpleNamespace(
            book=book, sim=SimpleNamespace(book=book),
            world_id=None, habitats=('river',), age=3,
            state='collapsed', id='TREE-TEST')
        policy = TreeProvisioningPolicy(tree)
        with patch.object(policy, '_refresh', side_effect=[ValueError('Book rejected decay'), None]) as refresh:
            with self.assertRaisesRegex(ValueError, 'Book rejected decay'):
                policy.tick()
            self.assertEqual(policy.last_age, -1)
            self.assertFalse(policy.tick())
            self.assertEqual(policy.last_age, 3)
            self.assertEqual(refresh.call_count, 2)
            self.assertFalse(policy.tick())
            self.assertEqual(refresh.call_count, 2)


if __name__ == '__main__':
    unittest.main()
