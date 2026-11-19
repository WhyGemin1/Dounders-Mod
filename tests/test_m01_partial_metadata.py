"""Core151 regression: rejected M01 adapter calls must not mutate Book metadata."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from founders_engine.checkpoint import save_checkpoint, load_checkpoint
from run_world_tree_pilot import bootstrap
from founders_engine.authority import SingleEngineSession


class PartialBookMutationTests(unittest.TestCase):
    def test_failed_harvest_poisoned_for_each_book_metadata_field(self):
        for field in ("last", "external", "toll_count"):
            with self.subTest(field=field):
                world, _, tree_id = bootstrap(438)
                session = SingleEngineSession(world, tree_id)
                before = session.audit()
                with TemporaryDirectory() as directory:
                    checkpoint = Path(directory) / 'core151.checkpoint'
                    save_checkpoint(world, tree_id, checkpoint)
                    checkpoint_bytes = checkpoint.read_bytes()
                    self._assert_partial_mutation_recovery(session, world, tree_id, field,
                                                           before, checkpoint, checkpoint_bytes)

    def _assert_partial_mutation_recovery(self, session, world, tree_id, field,
                                          before, checkpoint, checkpoint_bytes):
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

        self.assertEqual(checkpoint.read_bytes(), checkpoint_bytes)
        recovered = load_checkpoint(checkpoint, expected_tree_id=tree_id)
        proof = recovered.audit()
        self.assertEqual(proof.tick, before.tick)
        self.assertEqual(proof.book_sequence, before.book_sequence)
        self.assertEqual(proof.founder_count, 100)
        self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
        self.assertLessEqual(abs(proof.book_energy_error), 1e-6)
        self.assertIs(recovered.world.book, recovered.book)
        self.assertIs(recovered.world.founders.book, recovered.book)
        self.assertEqual(getattr(recovered.book, field), previous)
        # A clean replay from the same durable checkpoint is the reference outcome.
        baseline = load_checkpoint(checkpoint, expected_tree_id=tree_id)
        baseline.step()
        baseline_audit = baseline.audit()
        recovered.step()
        self.assertEqual(recovered.world.tick, before.tick + 1)
        self.assertEqual(recovered.world.tick, baseline.world.tick)
        self.assertEqual(recovered.book.seq, baseline.book.seq)
        self.assertEqual(dict(recovered.book.mass), dict(baseline.book.mass))
        self.assertEqual(dict(recovered.book.energy), dict(baseline.book.energy))
        self.assertEqual(recovered.book.request_receipts, baseline.book.request_receipts)
        self.assertEqual(recovered.book.transaction_history, baseline.book.transaction_history)
        self.assertEqual(recovered.book.last, baseline.book.last)
        self.assertEqual(recovered.book.external, baseline.book.external)
        self.assertEqual(recovered.book.toll_count, baseline.book.toll_count)
        post = recovered.audit()
        self.assertEqual(post.founder_count, 100)
        # The first recovered tick must preserve every pre-failure Founder key.
        self.assertEqual(len(recovered.world.founders.people), 100)
        self.assertEqual(set(recovered.world.founders.people), set(world.founders.people))
        self.assertEqual(set(recovered.world.founders.people),
                         set(baseline.world.founders.people))
        self.assertEqual(post.book_mass_error, baseline_audit.book_mass_error)
        self.assertEqual(post.book_energy_error, baseline_audit.book_energy_error)
        self.assertEqual(post.book_sequence, recovered.book.seq)
        self.assertLessEqual(abs(post.book_mass_error), 1e-6)
        self.assertLessEqual(abs(post.book_energy_error), 1e-6)
        self.assertIs(recovered.world.book, recovered.book)
        self.assertIs(recovered.world.founders.book, recovered.book)
        # Verify replay stays equivalent beyond the first post-restart world tick.
        baseline.step()
        recovered.step()
        self.assertEqual(recovered.world.tick, baseline.world.tick)
        self.assertEqual(recovered.book.seq, baseline.book.seq)
        self.assertEqual(dict(recovered.book.mass), dict(baseline.book.mass))
        self.assertEqual(dict(recovered.book.energy), dict(baseline.book.energy))
        self.assertEqual(recovered.book.transaction_history, baseline.book.transaction_history)
        self.assertEqual(recovered.book.request_receipts, baseline.book.request_receipts)
        # Replay equality must include settlement metadata, not only balances/history.
        self.assertEqual(recovered.book.last, baseline.book.last)
        self.assertEqual(recovered.book.external, baseline.book.external)
        self.assertEqual(recovered.book.toll_count, baseline.book.toll_count)
        self.assertIs(recovered.world.book, recovered.book)
        self.assertIs(baseline.world.book, baseline.book)
        second = recovered.audit()
        self.assertEqual(second.founder_count, 100)
        # Check actual Founder identities, not just their aggregate count.
        self.assertEqual(set(recovered.world.founders.people),
                         set(baseline.world.founders.people))
        self.assertEqual(set(recovered.world.founders.people),
                         set(world.founders.people))
        self.assertIs(recovered.world.founders.book, recovered.book)
        self.assertIs(baseline.world.founders.book, baseline.book)
        self.assertLessEqual(abs(second.book_mass_error), 1e-6)
        self.assertLessEqual(abs(second.book_energy_error), 1e-6)
        self.assertEqual(second.book_mass_error, baseline.audit().book_mass_error)
        self.assertEqual(second.book_energy_error, baseline.audit().book_energy_error)
        self.assertEqual(second.book_sequence, recovered.book.seq)
        self.assertIs(recovered.world.book, recovered.book)
        self.assertIs(recovered.world.founders.book, recovered.book)
        # A recovered session must never rewrite its original durable checkpoint.
        self.assertEqual(checkpoint.read_bytes(), checkpoint_bytes)
        durable_again = load_checkpoint(checkpoint, expected_tree_id=tree_id)
        durable_audit = durable_again.audit()
        self.assertEqual(durable_audit.tick, before.tick)
        self.assertEqual(durable_audit.book_sequence, before.book_sequence)
        self.assertEqual(set(durable_again.world.founders.people),
                         set(world.founders.people))
        self.assertIs(durable_again.world.book, durable_again.book)
        self.assertIs(durable_again.world.founders.book, durable_again.book)
        self.assertLessEqual(abs(durable_audit.book_mass_error), 1e-6)
        self.assertLessEqual(abs(durable_audit.book_energy_error), 1e-6)
        print(f"seed438 durable_unchanged field={field} "
              f"tick={durable_audit.tick} seq={durable_audit.book_sequence}")
        print(f"seed438 second_tick field={field} tick={second.tick} "
              f"seq={second.book_sequence} mass={second.book_mass_error:.17g} "
              f"energy={second.book_energy_error:.17g}")
        print(f"seed438 recovery field={field} tick={proof.tick}->{post.tick} "
              f"seq={proof.book_sequence}->{post.book_sequence} "
              f"mass={proof.book_mass_error:.17g}->{post.book_mass_error:.17g} "
              f"energy={proof.book_energy_error:.17g}->{post.book_energy_error:.17g}")
