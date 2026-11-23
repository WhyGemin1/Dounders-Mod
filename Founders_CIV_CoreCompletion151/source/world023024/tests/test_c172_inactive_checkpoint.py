"""C172: failed Book commit must not advance an inactive Tree checkpoint."""
import unittest
from contextlib import contextmanager
from types import SimpleNamespace
from founders_civ.core.ledger import Book
from founders_civ.core.autonomous_provisioning import TreeProvisioningPolicy


class CommitFailureBook(Book):
    @contextmanager
    def atomic_batch(self):
        with super().atomic_batch():
            yield
            raise RuntimeError("injected Book commit failure")


class InactiveCheckpointTests(unittest.TestCase):
    def test_inactive_tree_commit_failure_is_retryable(self):
        book = CommitFailureBook()
        book.freeze()
        sim = SimpleNamespace(
            book=book, seeds=SimpleNamespace(plants={"T": {"status": "stable"}})
        )
        tree = SimpleNamespace(
            book=book, sim=sim, world_id=None, habitats=("river",),
            age=1, state="collapsed", id="T"
        )
        policy = TreeProvisioningPolicy(tree)
        with self.assertRaisesRegex(RuntimeError, "injected Book commit failure"):
            policy.tick()
        self.assertEqual(policy.last_age, -1)
        self.assertEqual(policy.events, [])
        self.assertEqual(policy.lots, {})
        self.assertEqual(book.seq, 0)
        book.audit()

    def test_inactive_tree_successful_commit_advances_checkpoint_once(self):
        book = Book()
        book.freeze()
        sim = SimpleNamespace(
            book=book, seeds=SimpleNamespace(plants={"T": {"status": "stable"}})
        )
        tree = SimpleNamespace(
            book=book, sim=sim, world_id=None, habitats=("river",),
            age=1, state="collapsed", id="T"
        )
        policy = TreeProvisioningPolicy(tree)
        self.assertFalse(policy.tick())
        self.assertEqual(policy.last_age, 1)
        self.assertFalse(policy.tick())
        book.audit()


if __name__ == "__main__":
    unittest.main()
