"""Checkpoint envelope tests and actual Core151 restart tests."""
import tempfile
import unittest
from pathlib import Path
from founders_engine.checkpoint import _encode, _decode

class EnvelopeTests(unittest.TestCase):
    def test_roundtrip(self):
        self.assertEqual(_decode(_encode(b'abc')), b'abc')

    def test_corrupt_digest(self):
        data = bytearray(_encode(b'abc'))
        data[-1] ^= 1
        with self.assertRaisesRegex(ValueError, 'digest'):
            _decode(bytes(data))

    def test_truncated_payload(self):
        with self.assertRaisesRegex(ValueError, 'length'):
            _decode(_encode(b'abc')[:-1])

    def test_reject_foreign_format(self):
        with self.assertRaisesRegex(ValueError, 'format'):
            _decode(b'not a checkpoint')

class IntegratedCheckpointTests(unittest.TestCase):
    def setUp(self):
        from run_world_tree_pilot import bootstrap
        from founders_engine.authority import SingleEngineSession
        self.world, _, self.tree_id = bootstrap(400)
        self.session = SingleEngineSession(self.world, self.tree_id)

    def test_restart_replay_is_idempotent(self):
        from founders_engine.checkpoint import save_checkpoint, load_checkpoint
        first = self.session.harvest('F001', 'checkpoint-replay', '1',
                                     'forest', 'plant', .01, .001)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'state.cp'
            save_checkpoint(self.world, self.tree_id, path)
            restored = load_checkpoint(path, self.tree_id)
            before = restored.book.seq
            receipt = restored.harvest('F001', 'checkpoint-replay', '1',
                                       'forest', 'plant', .01, .001)
            self.assertEqual(receipt, first)
            self.assertEqual(restored.book.seq, before)
            self.assertEqual(restored.world.tick, self.world.tick)
            self.assertIs(restored.world.world_trees.worlds[self.tree_id].book,
                          restored.book)
            restored.audit()

    def test_reject_receipt_claiming_future_book_sequence(self):
        from dataclasses import replace
        from founders_engine.checkpoint import save_checkpoint
        self.session.harvest('F001', 'receipt-sequence', '1',
                             'forest', 'plant', .01, .001)
        book = self.session.book
        request_id = next(iter(book.request_receipts))
        legs, receipt = book.request_receipts[request_id]
        book.request_receipts[request_id] = (
            legs, replace(receipt, seq=book.seq + 1))
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'inconsistent Book replay receipt'):
                save_checkpoint(self.world, self.tree_id, Path(tmp) / 'invalid.cp')

    def test_reject_receipt_with_modified_transfer_legs(self):
        from founders_engine.checkpoint import save_checkpoint
        self.session.harvest('F001', 'receipt-legs', '1',
                             'forest', 'plant', .01, .001)
        book = self.session.book
        request_id = next(iter(book.request_receipts))
        legs, receipt = book.request_receipts[request_id]
        book.request_receipts[request_id] = (
            (legs[0], ()), receipt)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'inconsistent Book replay receipt'):
                save_checkpoint(self.world, self.tree_id, Path(tmp) / 'invalid.cp')

    def test_reject_two_request_ids_claiming_same_settlement(self):
        from founders_engine.checkpoint import save_checkpoint
        self.session.harvest('F001', 'receipt-collision', '1',
                             'forest', 'plant', .01, .001)
        book = self.session.book
        record = next(iter(book.request_receipts.values()))
        book.request_receipts['forged-request-id'] = record
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'duplicate Book settlement sequence'):
                save_checkpoint(self.world, self.tree_id, Path(tmp) / 'invalid.cp')

    def test_seed_428_checkpoint_restart_preserves_numerical_book_audit(self):
        """Compare real Core151 uninterrupted and disk-restored ticks and balances."""
        from run_world_tree_pilot import bootstrap
        from founders_engine.authority import SingleEngineSession
        from founders_engine.checkpoint import save_checkpoint, load_checkpoint

        world, _, tree_id = bootstrap(428)
        uninterrupted = SingleEngineSession(world, tree_id)
        initial = uninterrupted.audit()
        self.assertEqual(initial.founder_count, 100)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'seed428.cp'
            save_checkpoint(world, tree_id, path)
            restarted = load_checkpoint(path, tree_id)
            restored_initial = restarted.audit()
            self.assertEqual(restored_initial.tick, initial.tick)
            self.assertEqual(restored_initial.book_sequence, initial.book_sequence)
            for day in range(2):
                uninterrupted.step()
                restarted.step()
                direct = uninterrupted.audit()
                replay = restarted.audit()
                self.assertEqual((direct.tick, direct.book_sequence),
                                 (replay.tick, replay.book_sequence))
                self.assertEqual(dict(world.book.mass), dict(restarted.book.mass))
                self.assertEqual(dict(world.book.energy), dict(restarted.book.energy))
                self.assertEqual(frozenset(world.founders.people),
                                 frozenset(restarted.world.founders.people))
                for value in (direct.book_mass_error, direct.book_energy_error,
                              replay.book_mass_error, replay.book_energy_error):
                    self.assertLessEqual(abs(value), 1e-6)
                self.assertAlmostEqual(direct.book_mass_error,
                                       replay.book_mass_error, delta=1e-9)
                self.assertAlmostEqual(direct.book_energy_error,
                                       replay.book_energy_error, delta=1e-9)
                print('CORE151_RESTART_AUDIT seed=428 '
                      f'day={day + 1} tick={direct.tick} seq={direct.book_sequence} '
                      f'direct_mass={direct.book_mass_error:.17g} '
                      f'replay_mass={replay.book_mass_error:.17g} '
                      f'direct_energy={direct.book_energy_error:.17g} '
                      f'replay_energy={replay.book_energy_error:.17g}')
                save_checkpoint(restarted.world, tree_id, path)
                restarted = load_checkpoint(path, tree_id)
                durable = restarted.audit()
                self.assertEqual((durable.tick, durable.book_sequence),
                                 (direct.tick, direct.book_sequence))
                self.assertEqual(dict(world.book.mass), dict(restarted.book.mass))
                self.assertEqual(dict(world.book.energy), dict(restarted.book.energy))
                self.assertEqual(frozenset(world.founders.people),
                                 frozenset(restarted.world.founders.people))
                self.assertAlmostEqual(durable.book_mass_error,
                                       direct.book_mass_error, delta=1e-9)
                self.assertAlmostEqual(durable.book_energy_error,
                                       direct.book_energy_error, delta=1e-9)

    def test_restarted_and_uninterrupted_match(self):
        from founders_engine.checkpoint import save_checkpoint, load_checkpoint
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'state.cp'
            save_checkpoint(self.world, self.tree_id, path)
            restored = load_checkpoint(path, self.tree_id)
            self.session.step()
            restored.step()
            self.assertEqual(restored.world.tick, self.world.tick)
            self.assertEqual(restored.book.seq, self.world.book.seq)
            self.assertEqual(dict(restored.book.mass), dict(self.world.book.mass))
            self.assertEqual(dict(restored.book.energy), dict(self.world.book.energy))
            restored.audit()

if __name__ == '__main__':
    unittest.main()
