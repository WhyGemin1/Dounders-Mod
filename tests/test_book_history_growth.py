"""Canonical Core151 Book history growth gate; no shadow ledger or clock."""
import tempfile
import unittest
from pathlib import Path

from founders_engine.authority import SingleEngineSession
from founders_engine.checkpoint import load_checkpoint, save_checkpoint
from run_world_tree_pilot import bootstrap


class BookHistoryGrowthTests(unittest.TestCase):
    def test_history_grows_only_with_real_settlements_and_restart_preserves_it(self):
        world, _, tree_id = bootstrap(400)
        session = SingleEngineSession(world, tree_id)
        book = world.book
        self.assertIs(session.book, book)
        self.assertEqual(len(world.founders.people), 100)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "world.cp"
            sizes = []
            counts = []
            for i in range(16):
                if i:
                    session.checkpointed_harvest(
                        path, "F001", f"growth-{i}", "v1",
                        "forest", "plant", .01, .001)
                else:
                    save_checkpoint(world, tree_id, path)
                counts.append(len(book.transaction_history))
                sizes.append(path.stat().st_size)
                self.assertEqual(counts[-1], book.seq)
                audit = session.audit()
                self.assertLessEqual(abs(audit.book_mass_error), 1e-6)
                self.assertLessEqual(abs(audit.book_energy_error), 1e-6)
                restored = load_checkpoint(path, tree_id)
                self.assertEqual(restored.book.transaction_history, book.transaction_history)
                self.assertEqual(restored.book.seq, book.seq)
                self.assertIs(restored.world.founders.book, restored.book)
                # Replaying a durable claim after restart must not grow history.
                if i:
                    replay_session = SingleEngineSession(restored.world, tree_id)
                    before_seq = restored.book.seq
                    before_history = list(restored.book.transaction_history)
                    before_audit = replay_session.audit()
                    replay_session.harvest("F001", f"growth-{i}", "v1",
                                           "forest", "plant", .01, .001)
                    self.assertEqual(restored.book.seq, before_seq)
                    self.assertEqual(restored.book.transaction_history, before_history)
                    after_audit = replay_session.audit()
                    self.assertEqual(after_audit.book_mass_error, before_audit.book_mass_error)
                    self.assertEqual(after_audit.book_energy_error, before_audit.book_energy_error)
            self.assertEqual(counts[-1] - counts[0], 15)
            self.assertTrue(all(b > a for a, b in zip(sizes, sizes[1:])))
            increments = [b - a for a, b in zip(sizes, sizes[1:])]
            self.assertTrue(all(delta > 0 for delta in increments))
            print("BOOK_HISTORY_GROWTH", "sequences=", counts,
                  "checkpoint_bytes=", sizes,
                  "delta_bytes=", sizes[-1] - sizes[0],
                  "per_settlement_bytes=", increments, flush=True)
