"""Core151 regression: rejected M01 adapter calls must not mutate Book metadata."""
import unittest
from run_world_tree_pilot import bootstrap
from founders_engine.authority import SingleEngineSession


class PartialBookMutationTests(unittest.TestCase):
    def test_failed_harvest_poisoned_for_each_book_metadata_field(self):
        for field in ("last", "external", "toll_count"):
            with self.subTest(field=field):
                world, _, tree_id = bootstrap(438)
                session = SingleEngineSession(world, tree_id)
                before = session.audit()
                original = session.gateway.founder_harvest
                previous = getattr(session.book, field)

                def partial_failure(*args, **kwargs):
                    if field == "last":
                        session.book.last = None if previous is not None else "corrupt"
                    else:
                        setattr(session.book, field, previous + 1)
                    raise ValueError("simulated partial Book metadata mutation")

                session.gateway.founder_harvest = partial_failure
                try:
                    with self.assertRaisesRegex(ValueError, "simulated partial"):
                        session.harvest("F001", "metadata-failure", "1",
                                        "forest", "plant", .01, .001)
                finally:
                    session.gateway.founder_harvest = original
                self.assertNotEqual(getattr(session.book, field), previous)
                self.assertEqual(session.book.seq, before.book_sequence)
                self.assertEqual(world.tick, before.tick)
                with self.assertRaisesRegex(RuntimeError, "checkpoint outcome uncertain"):
                    session.harvest("F001", "after-failure", "1",
                                    "forest", "plant", .01, .001)
