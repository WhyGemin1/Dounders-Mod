"""Canonical Core151 Book history growth gate; no shadow ledger or clock."""
import tempfile
import unittest
from pathlib import Path

from founders_engine.authority import SingleEngineSession
from founders_engine.checkpoint import load_checkpoint, save_checkpoint
from run_world_tree_pilot import bootstrap


class BookHistoryGrowthTests(unittest.TestCase):
    def test_boolean_world_clock_rejected_without_checkpoint_mutation(self):
        world, _, tree_id = bootstrap(400)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "world.cp"
            save_checkpoint(world, tree_id, path)
            original_bytes = path.read_bytes()
            original_tick = world.tick
            original_seq = world.book.seq
            original_history = list(world.book.transaction_history)
            # A checksum-valid object graph cannot turn a Boolean into a clock.
            # Preserve the original checkpoint and canonical Book on rejection.
            world.tick = True
            world.ecology.day = True
            with self.assertRaisesRegex(ValueError, "invalid canonical world clock"):
                save_checkpoint(world, tree_id, path)
            self.assertEqual(path.read_bytes(), original_bytes)
            self.assertEqual(world.book.seq, original_seq)
            self.assertEqual(world.book.transaction_history, original_history)
            world.tick = original_tick
            world.ecology.day = original_tick
            restored = load_checkpoint(path, tree_id)
            self.assertEqual(restored.world.tick, original_tick)
            self.assertEqual(len(restored.world.founders.people), 100)

    def test_world_clock_tampering_fails_closed_without_checkpoint_mutation(self):
        # Reject invalid world.tick independently of the ecology clock.
        world, _, tree_id = bootstrap(400)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "world.cp"
            save_checkpoint(world, tree_id, path)
            original_bytes = path.read_bytes()
            original_tick = world.tick
            original_seq = world.book.seq
            original_history = list(world.book.transaction_history)
            for invalid_tick, expected_error in ((-1, "invalid canonical world clock"),
                                                 (0.5, "invalid canonical world clock"),
                                                 (True, "invalid canonical world clock"),
                                                 (original_tick + 1, "ecology and Founder clocks disagree")):
                with self.subTest(world_tick=invalid_tick):
                    world.tick = invalid_tick
                    with self.assertRaisesRegex(ValueError, expected_error):
                        save_checkpoint(world, tree_id, path)
                    self.assertEqual(path.read_bytes(), original_bytes)
                    self.assertEqual(world.book.seq, original_seq)
                    self.assertEqual(world.book.transaction_history, original_history)
            world.tick = original_tick
            restored = load_checkpoint(path, tree_id)
            self.assertEqual(restored.world.tick, original_tick)
            self.assertIs(restored.world.founders.book, restored.book)
            self.assertEqual(len(restored.world.founders.people), 100)

    def test_ecology_clock_tampering_fails_closed_without_book_or_checkpoint_mutation(self):
        # Independently exercise ecology.day; a matching world.tick is not
        # sufficient if the ecology clock is Boolean, negative, or divergent.
        world, _, tree_id = bootstrap(400)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "world.cp"
            save_checkpoint(world, tree_id, path)
            original_bytes = path.read_bytes()
            original_tick = world.tick
            original_seq = world.book.seq
            original_history = list(world.book.transaction_history)
            for invalid_day, message in (
                (True, "invalid canonical world clock"),
                (-1, "invalid canonical world clock"),
                (original_tick + 1, "ecology and Founder clocks disagree"),
            ):
                with self.subTest(ecology_day=invalid_day):
                    world.ecology.day = invalid_day
                    with self.assertRaisesRegex(ValueError, message):
                        save_checkpoint(world, tree_id, path)
                    self.assertEqual(path.read_bytes(), original_bytes)
                    self.assertEqual(world.book.seq, original_seq)
                    self.assertEqual(world.book.transaction_history, original_history)
            world.ecology.day = original_tick
            restored = load_checkpoint(path, tree_id)
            self.assertEqual(restored.world.tick, original_tick)
            self.assertEqual(restored.world.ecology.day, original_tick)
            self.assertEqual(len(restored.world.founders.people), 100)

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
                # Restored snapshots must retain the original Founder roster and world clock.
                self.assertEqual(set(restored.world.founders.people), set(world.founders.people))
                self.assertEqual(len(restored.world.founders.people), 100)
                self.assertEqual(restored.world.tick, world.tick)
                restored_audit = SingleEngineSession(restored.world, tree_id).audit()
                self.assertLessEqual(abs(restored_audit.book_mass_error), 1e-6)
                self.assertLessEqual(abs(restored_audit.book_energy_error), 1e-6)
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
