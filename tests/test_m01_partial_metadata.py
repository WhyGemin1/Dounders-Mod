"""Real Core151 regression: a failed M01 adapter must not silently alter Book metadata."""
import unittest
from run_world_tree_pilot import bootstrap
from founders_engine.authority import SingleEngineSession


class PartialBookMutationTests(unittest.TestCase):
    def test_failed_harvest_poisoned_when_last_transaction_changes_without_seq(self):
        world, _, tree_id = bootstrap(438)
        session = SingleEngineSession(world, tree_id)
        before = session.audit()
        original = session.gateway.founder_harvest

        def partial_failure(*args, **kwargs):
            session.book.last = None
            raise ValueError("simulated partial Book metadata mutation")

        session.gateway.founder_harvest = partial_failure
        try:
            with self.assertRaisesRegex(ValueError, "simulated partial"):
                session.harvest("F001", "metadata-failure", "1", "forest", "plant", .01, .001)
        finally:
            session.gateway.founder_harvest = original
        self.assertEqual(session.book.seq, before.book_sequence)
        self.assertEqual(world.tick, before.tick)
        with self.assertRaisesRegex(RuntimeError, "checkpoint outcome uncertain"):
            session.harvest("F001", "after-failure", "1", "forest", "plant", .01, .001)
