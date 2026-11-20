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

    def test_reject_book_transaction_counter_drift(self):
        from founders_engine.checkpoint import save_checkpoint
        self.session.book.transactions += 1
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'counters disagree'):
                save_checkpoint(self.world, self.tree_id, Path(tmp) / 'state.cp')

    def test_reject_book_toll_counter_drift(self):
        from founders_engine.checkpoint import save_checkpoint
        self.session.book.toll_count += 1
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'counters disagree'):
                save_checkpoint(self.world, self.tree_id, Path(tmp) / 'state.cp')

    def test_book_move_once_rejects_counter_drift_before_new_settlement(self):
        # The live Book must fail closed before a corrupted checkpoint is saved.
        book = self.session.book
        for field in ('transactions', 'toll_count'):
            with self.subTest(field=field):
                prior = getattr(book, field)
                seq = book.seq
                tick = self.world.tick
                founder_ids = set(self.world.founders.people)
                self.assertEqual(len(founder_ids), 100)
                mass = dict(book.mass)
                energy = dict(book.energy)
                receipts = dict(book.request_receipts)
                history = list(book.transaction_history)
                try:
                    setattr(book, field, prior + 1)
                    with self.assertRaisesRegex(ValueError, 'counters disagree'):
                        book.move_once('counter-drift-' + field)
                    self.assertEqual(book.seq, seq)
                    self.assertEqual(self.world.tick, tick)
                    self.assertEqual(set(self.world.founders.people), founder_ids)
                    self.assertIs(self.world.book, book)
                    self.assertIs(self.world.founders.book, book)
                    self.assertEqual(dict(book.mass), mass)
                    self.assertEqual(dict(book.energy), energy)
                    self.assertEqual(book.request_receipts, receipts)
                    self.assertEqual(book.transaction_history, history)
                finally:
                    setattr(book, field, prior)
                proof = self.session.audit()
                self.assertEqual(proof.founder_count, 100)
                self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
                self.assertLessEqual(abs(proof.book_energy_error), 1e-6)
                print('CORE151_LIVE_COUNTER_DRIFT '
                      f'field={field} tick={proof.tick} seq={proof.book_sequence} '
                      f'mass={proof.book_mass_error:.17g} '
                      f'energy={proof.book_energy_error:.17g}')

    def test_replay_receipt_rejects_counter_drift_without_mutation(self):
        book = self.session.book
        args = ('F001', 'counter-replay-guard', '1', 'forest', 'plant', .01, .001)
        original = self.session.harvest(*args)
        for field in ('transactions', 'toll_count'):
            with self.subTest(field=field):
                prior = getattr(book, field)
                snapshot = (book.seq, self.world.tick, dict(book.mass),
                            dict(book.energy), dict(book.request_receipts),
                            list(book.transaction_history),
                            frozenset(self.world.founders.people))
                try:
                    setattr(book, field, prior + 1)
                    with self.assertRaisesRegex(ValueError, 'counters disagree'):
                        self.session.harvest(*args)
                    self.assertEqual(snapshot, (book.seq, self.world.tick,
                        dict(book.mass), dict(book.energy),
                        dict(book.request_receipts), list(book.transaction_history),
                        frozenset(self.world.founders.people)))
                finally:
                    setattr(book, field, prior)
                self.assertEqual(self.session.harvest(*args), original)
                proof = self.session.audit()
                self.assertEqual(proof.founder_count, 100)
                self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
                self.assertLessEqual(abs(proof.book_energy_error), 1e-6)

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

    def test_seed_429_m01_receipt_survives_tick_and_second_restart(self):
        """Real Core151 Book settlement must remain exactly-once across ticks and disk reloads."""
        from run_world_tree_pilot import bootstrap
        from founders_engine.authority import SingleEngineSession
        from founders_engine.checkpoint import save_checkpoint, load_checkpoint

        world, _, tree_id = bootstrap(429)
        session = SingleEngineSession(world, tree_id)
        args = ('F001', 'seed429-durable-harvest', '1',
                'forest', 'plant', .01, .001)
        original = session.harvest(*args)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'seed429.cp'
            save_checkpoint(world, tree_id, path)
            restored = load_checkpoint(path, tree_id)
            seq_before_replay = restored.book.seq
            self.assertEqual(restored.harvest(*args), original)
            self.assertEqual(restored.book.seq, seq_before_replay)
            before = restored.audit()
            self.assertEqual(before.founder_count, 100)
            restored.step()
            after = restored.audit()
            self.assertEqual(after.tick, before.tick + 1)
            self.assertGreaterEqual(after.book_sequence, seq_before_replay)
            save_checkpoint(restored.world, tree_id, path)
            reloaded = load_checkpoint(path, tree_id)
            seq_after_restart = reloaded.book.seq
            self.assertEqual(reloaded.harvest(*args), original)
            self.assertEqual(reloaded.book.seq, seq_after_restart)
            durable = reloaded.audit()
            self.assertEqual((durable.tick, durable.book_sequence),
                             (after.tick, after.book_sequence))
            self.assertEqual(dict(reloaded.book.mass), dict(restored.book.mass))
            self.assertEqual(dict(reloaded.book.energy), dict(restored.book.energy))
            for residual in (before.book_mass_error, before.book_energy_error,
                             after.book_mass_error, after.book_energy_error,
                             durable.book_mass_error, durable.book_energy_error):
                self.assertLessEqual(abs(residual), 1e-6)
            print('CORE151_M01_RESTART seed=429 '
                  f'tick={durable.tick} seq={durable.book_sequence} '
                  f'mass={durable.book_mass_error:.17g} '
                  f'energy={durable.book_energy_error:.17g}')

    def test_seed_430_replayed_receipt_cannot_change_quantity_after_restart(self):
        """A reused M01 request ID cannot change its Book-funded transfer."""
        from run_world_tree_pilot import bootstrap
        from founders_engine.authority import SingleEngineSession
        from founders_engine.checkpoint import save_checkpoint, load_checkpoint

        world, _, tree_id = bootstrap(430)
        session = SingleEngineSession(world, tree_id)
        args = ('F001', 'seed430-replay-binding', '1',
                'forest', 'plant', .01, .001)
        original = session.harvest(*args)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'seed430.cp'
            save_checkpoint(world, tree_id, path)
            restored = load_checkpoint(path, tree_id)
            restored.step()
            save_checkpoint(restored.world, tree_id, path)
            reloaded = load_checkpoint(path, tree_id)
            before_seq = reloaded.book.seq
            before_mass = dict(reloaded.book.mass)
            before_energy = dict(reloaded.book.energy)
            before_receipts = dict(reloaded.book.request_receipts)
            before_tick = reloaded.world.tick
            with self.assertRaises(ValueError):
                reloaded.harvest(*args[:-2], .02, .001)
            self.assertEqual(reloaded.book.seq, before_seq)
            self.assertEqual(dict(reloaded.book.mass), before_mass)
            self.assertEqual(dict(reloaded.book.energy), before_energy)
            self.assertEqual(dict(reloaded.book.request_receipts), before_receipts)
            self.assertEqual(reloaded.world.tick, before_tick)
            self.assertEqual(reloaded.harvest(*args), original)
            self.assertEqual(reloaded.book.seq, before_seq)
            proof = reloaded.audit()
            self.assertEqual(proof.founder_count, 100)
            self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
            self.assertLessEqual(abs(proof.book_energy_error), 1e-6)

    def test_seed_431_replayed_receipt_cannot_change_energy_after_restart(self):
        """A durable M01 request cannot change energy while preserving mass."""
        from run_world_tree_pilot import bootstrap
        from founders_engine.authority import SingleEngineSession
        from founders_engine.checkpoint import save_checkpoint, load_checkpoint

        world, _, tree_id = bootstrap(431)
        session = SingleEngineSession(world, tree_id)
        args = ('F001', 'seed431-energy-binding', '1',
                'forest', 'plant', .01, .001)
        original = session.harvest(*args)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'seed431.cp'
            save_checkpoint(world, tree_id, path)
            restarted = load_checkpoint(path, tree_id)
            restarted.step()
            save_checkpoint(restarted.world, tree_id, path)
            durable = load_checkpoint(path, tree_id)
            seq = durable.book.seq
            tick = durable.world.tick
            mass = dict(durable.book.mass)
            energy = dict(durable.book.energy)
            receipts = dict(durable.book.request_receipts)
            with self.assertRaises(ValueError):
                durable.harvest(*args[:-1], .002)
            self.assertEqual(durable.book.seq, seq)
            self.assertEqual(durable.world.tick, tick)
            self.assertEqual(dict(durable.book.mass), mass)
            self.assertEqual(dict(durable.book.energy), energy)
            self.assertEqual(dict(durable.book.request_receipts), receipts)
            self.assertEqual(durable.harvest(*args), original)
            self.assertEqual(durable.book.seq, seq)
            proof = durable.audit()
            self.assertEqual(proof.founder_count, 100)
            self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
            self.assertLessEqual(abs(proof.book_energy_error), 1e-6)
            print('CORE151_M01_ENERGY_REPLAY seed=431 '
                  f'tick={proof.tick} seq={proof.book_sequence} '
                  f'mass={proof.book_mass_error:.17g} '
                  f'energy={proof.book_energy_error:.17g}')


    def test_seed_432_replayed_receipt_cannot_change_material_after_restart(self):
        """One M01 request cannot redirect a durable settlement to another resource."""
        from run_world_tree_pilot import bootstrap
        from founders_engine.authority import SingleEngineSession
        from founders_engine.checkpoint import save_checkpoint, load_checkpoint

        world, _, tree_id = bootstrap(432)
        session = SingleEngineSession(world, tree_id)
        args = ('F001', 'seed432-material-binding', '1',
                'forest', 'plant', .01, .001)
        original = session.harvest(*args)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'seed432.cp'
            save_checkpoint(world, tree_id, path)
            restored = load_checkpoint(path, tree_id)
            restored.step()
            save_checkpoint(restored.world, tree_id, path)
            durable = load_checkpoint(path, tree_id)
            seq, tick = durable.book.seq, durable.world.tick
            mass = dict(durable.book.mass)
            energy = dict(durable.book.energy)
            receipts = dict(durable.book.request_receipts)
            with self.assertRaises(ValueError):
                durable.harvest(*args[:4], 'detritus', *args[5:])
            self.assertEqual(durable.book.seq, seq)
            self.assertEqual(durable.world.tick, tick)
            self.assertEqual(dict(durable.book.mass), mass)
            self.assertEqual(dict(durable.book.energy), energy)
            self.assertEqual(dict(durable.book.request_receipts), receipts)
            self.assertEqual(durable.harvest(*args), original)
            self.assertEqual(durable.book.seq, seq)
            proof = durable.audit()
            self.assertEqual(proof.founder_count, 100)
            self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
            self.assertLessEqual(abs(proof.book_energy_error), 1e-6)
            print('CORE151_M01_MATERIAL_REPLAY seed=432 '
                  f'tick={proof.tick} seq={proof.book_sequence} '
                  f'mass={proof.book_mass_error:.17g} '
                  f'energy={proof.book_energy_error:.17g}')

    def test_seed_433_replayed_receipt_cannot_change_founder_after_restart(self):
        """A settled M01 request cannot be reassigned to a different Founder."""
        from run_world_tree_pilot import bootstrap
        from founders_engine.authority import SingleEngineSession
        from founders_engine.checkpoint import save_checkpoint, load_checkpoint

        world, _, tree_id = bootstrap(433)
        session = SingleEngineSession(world, tree_id)
        args = ('F001', 'seed433-founder-binding', '1',
                'forest', 'plant', .01, .001)
        original = session.harvest(*args)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'seed433.cp'
            save_checkpoint(world, tree_id, path)
            restored = load_checkpoint(path, tree_id)
            restored.step()
            save_checkpoint(restored.world, tree_id, path)
            durable = load_checkpoint(path, tree_id)
            seq, tick = durable.book.seq, durable.world.tick
            mass = dict(durable.book.mass)
            energy = dict(durable.book.energy)
            receipts = dict(durable.book.request_receipts)
            with self.assertRaises(ValueError):
                durable.harvest('F002', *args[1:])
            self.assertEqual(durable.book.seq, seq)
            self.assertEqual(durable.world.tick, tick)
            self.assertEqual(dict(durable.book.mass), mass)
            self.assertEqual(dict(durable.book.energy), energy)
            self.assertEqual(dict(durable.book.request_receipts), receipts)
            self.assertEqual(durable.harvest(*args), original)
            self.assertEqual(durable.book.seq, seq)
            proof = durable.audit()
            self.assertEqual(proof.founder_count, 100)
            self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
            self.assertLessEqual(abs(proof.book_energy_error), 1e-6)
            print('CORE151_M01_FOUNDER_REPLAY seed=433 '
                  f'tick={proof.tick} seq={proof.book_sequence} '
                  f'mass={proof.book_mass_error:.17g} '
                  f'energy={proof.book_energy_error:.17g}')

    def test_seed_434_ambiguous_receipt_identity_rejected_after_restart(self):
        """Colon-separated M01 source/revision aliases must not share a receipt."""
        from run_world_tree_pilot import bootstrap
        from founders_engine.authority import SingleEngineSession
        from founders_engine.checkpoint import save_checkpoint, load_checkpoint

        world, _, tree_id = bootstrap(434)
        session = SingleEngineSession(world, tree_id)
        original = session.harvest('F001', 'seed434-source', '1',
                                   'forest', 'plant', .01, .001)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'seed434.cp'
            save_checkpoint(world, tree_id, path)
            durable = load_checkpoint(path, tree_id)
            before = (durable.book.seq, durable.world.tick,
                      dict(durable.book.mass), dict(durable.book.energy),
                      dict(durable.book.request_receipts))
            for source, revision in (('seed434:source', '1'),
                                     ('seed434', 'source:1')):
                with self.assertRaises(ValueError):
                    durable.harvest('F001', source, revision,
                                    'forest', 'plant', .01, .001)
            self.assertEqual(
                (durable.book.seq, durable.world.tick,
                 dict(durable.book.mass), dict(durable.book.energy),
                 dict(durable.book.request_receipts)), before)
            self.assertEqual(durable.harvest('F001', 'seed434-source', '1',
                                            'forest', 'plant', .01, .001), original)
            proof = durable.audit()
            self.assertEqual(proof.founder_count, 100)
            self.assertLessEqual(abs(proof.book_mass_error), 1e-6)
            self.assertLessEqual(abs(proof.book_energy_error), 1e-6)
            print('CORE151_M01_IDENTITY_DELIMITER seed=434 '
                  f'tick={proof.tick} seq={proof.book_sequence} '
                  f'mass={proof.book_mass_error:.17g} '
                  f'energy={proof.book_energy_error:.17g}')

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
