"""Fault-injection gates for the actual Core151 Book/checkpoint M01 boundary.

A returned receipt proves local durable checkpoint, NOT native WorldBox ACK.
"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from founders_engine.authority import SingleEngineSession
from founders_engine.checkpoint import load_checkpoint, save_checkpoint
from run_world_tree_pilot import bootstrap


class DurableHarvestTests(unittest.TestCase):
    def setUp(self):
        self.world, _, self.tree_id = bootstrap(400)
        self.session = SingleEngineSession(self.world, self.tree_id)

    def test_successful_checkpointed_harvest_survives_restart_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'world.cp'
            before = self.session.book.seq
            receipt = self.session.checkpointed_harvest(
                path, 'F001', 'durable-claim', 'v1', 'forest', 'plant', .01, .001)
            self.assertEqual(self.session.book.seq, before + 1)
            restored = load_checkpoint(path, self.tree_id)
            self.assertEqual(restored.world.tick, self.world.tick)
            self.assertEqual(restored.book.seq, self.session.book.seq)
            self.assertEqual(dict(restored.book.mass), dict(self.session.book.mass))
            self.assertEqual(dict(restored.book.energy), dict(self.session.book.energy))
            self.assertIs(restored.world.founders.book, restored.book)
            self.assertEqual(len(restored.world.founders.people), 100)
            self.assertEqual(
                restored.checkpointed_harvest(
                    path, 'F001', 'durable-claim', 'v1',
                    'forest', 'plant', .01, .001), receipt)
            self.assertEqual(restored.book.seq, before + 1)
            restored.audit()
            load_checkpoint(path, self.tree_id).audit()

    def test_interruption_after_settlement_before_checkpoint_requires_reload(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'world.cp'
            save_checkpoint(self.world, self.tree_id, path)
            original_bytes = path.read_bytes()
            initial_seq = self.session.book.seq
            with patch('founders_engine.checkpoint.save_checkpoint',
                       side_effect=OSError('simulated disk interruption')):
                with self.assertRaisesRegex(OSError, 'simulated disk interruption'):
                    self.session.checkpointed_harvest(
                        path, 'F001', 'interrupted-claim', 'v1',
                        'forest', 'plant', .01, .001)
            # RAM may have settled, but durable Book has not. Never ACK RAM.
            self.assertEqual(self.session.book.seq, initial_seq + 1)
            self.assertEqual(path.read_bytes(), original_bytes)
            with self.assertRaisesRegex(RuntimeError, 'reload durable world'):
                self.session.step()
            with self.assertRaisesRegex(RuntimeError, 'reload durable world'):
                self.session.harvest('F002', 'other', 'v1',
                                     'forest', 'plant', .01)
            with self.assertRaisesRegex(RuntimeError, 'reload durable world'):
                self.session.checkpointed_harvest(
                    path, 'F001', 'interrupted-claim', 'v1',
                    'forest', 'plant', .01, .001)
            recovered = load_checkpoint(path, self.tree_id)
            self.assertEqual(recovered.book.seq, initial_seq)
            self.assertNotIn(
                f'm01:{self.tree_id}:interrupted-claim:v1',
                recovered.book.request_receipts)
            recovered.checkpointed_harvest(
                path, 'F001', 'interrupted-claim', 'v1',
                'forest', 'plant', .01, .001)
            self.assertEqual(recovered.book.seq, initial_seq + 1)
            self.assertEqual(load_checkpoint(path, self.tree_id).book.seq,
                             initial_seq + 1)
            recovered.book.audit()

    def test_invalid_request_does_not_poison_session_or_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'world.cp'
            save_checkpoint(self.world, self.tree_id, path)
            before = path.read_bytes()
            seq = self.session.book.seq
            with self.assertRaises(ValueError):
                self.session.checkpointed_harvest(
                    path, 'FAKE', 'invalid', 'v1', 'forest', 'plant', .01)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(self.session.book.seq, seq)
            self.session.audit()


    def test_restored_book_conservation_after_funded_harvest_and_tick(self):
        """Numerical mass/energy residuals must survive real Book settlement and restart."""
        import math
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'world.cp'
            before = self.session.audit()
            receipt = self.session.checkpointed_harvest(
                path, 'F001', 'audit-restart', 'v1',
                'forest', 'plant', .01, .001)
            after = self.session.audit()
            restored = load_checkpoint(path, self.tree_id)
            replay = restored.checkpointed_harvest(
                path, 'F001', 'audit-restart', 'v1',
                'forest', 'plant', .01, .001)
            self.assertEqual(receipt, replay)
            self.assertEqual(after.book_sequence, restored.book.seq)
            self.assertEqual(before.tick, restored.world.tick)
            self.assertEqual(dict(restored.book.mass), dict(self.session.book.mass))
            self.assertEqual(dict(restored.book.energy), dict(self.session.book.energy))
            for label, snapshot in (('before', before), ('settled', after),
                                    ('restored', restored.audit())):
                with self.subTest(stage=label):
                    self.assertTrue(math.isfinite(snapshot.book_mass_error))
                    self.assertTrue(math.isfinite(snapshot.book_energy_error))
                    self.assertLessEqual(abs(snapshot.book_mass_error), 1e-6)
                    self.assertLessEqual(abs(snapshot.book_energy_error), 1e-6)
                print('BOOK_AUDIT', label,
                      'mass_error=', repr(snapshot.book_mass_error),
                      'energy_error=', repr(snapshot.book_energy_error),
                      'seq=', snapshot.book_sequence, flush=True)
            restored.step()
            advanced = restored.audit()
            self.assertEqual(advanced.tick, before.tick + 1)
            self.assertEqual(advanced.founder_count, 100)
            self.assertLessEqual(abs(advanced.book_mass_error), 1e-6)
            self.assertLessEqual(abs(advanced.book_energy_error), 1e-6)
            print('BOOK_AUDIT stepped',
                  'mass_error=', repr(advanced.book_mass_error),
                  'energy_error=', repr(advanced.book_energy_error),
                  'seq=', advanced.book_sequence, flush=True)

    def test_corrupt_receipt_in_valid_envelope_rejected_without_settlement(self):
        """Trusted checkpoint with valid digest but impossible Book receipt fails closed."""
        import pickle
        from founders_engine.checkpoint import _encode
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'world.cp'
            self.session.checkpointed_harvest(
                path, 'F001', 'corrupt-receipt', 'v1',
                'forest', 'plant', .01, .001)
            clean_bytes = path.read_bytes()
            clean_seq = self.session.book.seq
            clean_mass = dict(self.session.book.mass)
            clean_energy = dict(self.session.book.energy)
            key = f'm01:{self.tree_id}:corrupt-receipt:v1'
            legs, receipt = self.session.book.request_receipts[key]
            from dataclasses import replace
            self.session.book.request_receipts[key] = (
                legs, replace(receipt, seq=clean_seq + 1))
            path.write_bytes(_encode(pickle.dumps(
                (self.tree_id, self.world), protocol=pickle.HIGHEST_PROTOCOL)))
            forged_bytes = path.read_bytes()
            self.assertNotEqual(forged_bytes, clean_bytes)
            with self.assertRaisesRegex(ValueError, 'inconsistent Book replay receipt'):
                load_checkpoint(path, self.tree_id)
            self.assertEqual(path.read_bytes(), forged_bytes)
            self.assertEqual(self.session.book.seq, clean_seq)
            self.assertEqual(dict(self.session.book.mass), clean_mass)
            self.assertEqual(dict(self.session.book.energy), clean_energy)
            with self.assertRaisesRegex(ValueError, 'inconsistent Book replay receipt'):
                save_checkpoint(self.world, self.tree_id, path)
            self.assertEqual(path.read_bytes(), forged_bytes)


    def test_historical_receipt_forgery_rejected_after_later_book_move(self):
        """A valid older sequence cannot impersonate another Book transfer."""
        import pickle
        from dataclasses import replace
        from founders_engine.checkpoint import _encode
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'world.cp'
            self.session.checkpointed_harvest(
                path, 'F001', 'older-receipt', 'v1',
                'forest', 'plant', .01, .001)
            key = f'm01:{self.tree_id}:older-receipt:v1'
            legs, receipt = self.session.book.request_receipts[key]
            # Advance canonical history beyond the receipt using the same Book.
            self.session.step()
            self.assertLess(receipt.seq, self.session.book.seq)
            clean_seq = self.session.book.seq
            clean_mass = dict(self.session.book.mass)
            clean_energy = dict(self.session.book.energy)
            fake_material = tuple((src, dst, qty * .5)
                                  for src, dst, qty in legs[0])
            self.session.book.request_receipts[key] = (
                (fake_material, legs[1]),
                replace(receipt, material=fake_material))
            path.write_bytes(_encode(pickle.dumps(
                (self.tree_id, self.world), protocol=pickle.HIGHEST_PROTOCOL)))
            forged_bytes = path.read_bytes()
            with self.assertRaisesRegex(ValueError, 'canonical Book transaction history'):
                load_checkpoint(path, self.tree_id)
            with self.assertRaisesRegex(ValueError, 'canonical Book transaction history'):
                save_checkpoint(self.world, self.tree_id, path)
            self.assertEqual(path.read_bytes(), forged_bytes)
            self.assertEqual(self.session.book.seq, clean_seq)
            self.assertEqual(dict(self.session.book.mass), clean_mass)
            self.assertEqual(dict(self.session.book.energy), clean_energy)

    def test_legacy_checkpoint_without_book_history_fails_closed(self):
        """No inferred transaction history from balances, even with valid checksum."""
        import pickle
        from founders_engine.checkpoint import _encode
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'legacy.cp'
            self.session.checkpointed_harvest(
                path, 'F001', 'legacy-claim', 'v1',
                'forest', 'plant', .01, .001)
            clean_seq = self.session.book.seq
            clean_mass = dict(self.session.book.mass)
            clean_energy = dict(self.session.book.energy)
            del self.session.book.transaction_history
            path.write_bytes(_encode(pickle.dumps(
                (self.tree_id, self.world), protocol=pickle.HIGHEST_PROTOCOL)))
            legacy_bytes = path.read_bytes()
            with self.assertRaisesRegex(ValueError, 'reviewed migration required'):
                load_checkpoint(path, self.tree_id)
            with self.assertRaisesRegex(ValueError, 'reviewed migration required'):
                save_checkpoint(self.world, self.tree_id, path)
            self.assertEqual(path.read_bytes(), legacy_bytes)
            self.assertEqual(self.session.book.seq, clean_seq)
            self.assertEqual(dict(self.session.book.mass), clean_mass)
            self.assertEqual(dict(self.session.book.energy), clean_energy)

    def test_checksum_valid_latest_receipt_cannot_impersonate_book_transaction(self):
        """A self-consistent forged receipt at the real last seq is not authentic."""
        import pickle
        from dataclasses import replace
        from founders_engine.checkpoint import _encode
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'world.cp'
            self.session.checkpointed_harvest(
                path, 'F001', 'latest-forgery', 'v1',
                'forest', 'plant', .01, .001)
            key = f'm01:{self.tree_id}:latest-forgery:v1'
            original_seq = self.session.book.seq
            original_mass = dict(self.session.book.mass)
            original_energy = dict(self.session.book.energy)
            legs, receipt = self.session.book.request_receipts[key]
            fake_material = tuple((s, t, q * .5) for s, t, q in legs[0])
            fake_legs = (fake_material, legs[1])
            forged_receipt = replace(receipt, material=fake_material)
            self.assertEqual(forged_receipt.seq, original_seq)
            self.assertNotEqual(forged_receipt, self.session.book.last)
            self.session.book.request_receipts[key] = (fake_legs, forged_receipt)
            path.write_bytes(_encode(pickle.dumps(
                (self.tree_id, self.world), protocol=pickle.HIGHEST_PROTOCOL)))
            forged_bytes = path.read_bytes()
            with self.assertRaisesRegex(ValueError, 'canonical Book transaction history'):
                load_checkpoint(path, self.tree_id)
            with self.assertRaisesRegex(ValueError, 'receipt does not match canonical Book transaction history'):
                save_checkpoint(self.world, self.tree_id, path)
            self.assertEqual(path.read_bytes(), forged_bytes)
            self.assertEqual(self.session.book.seq, original_seq)
            self.assertEqual(dict(self.session.book.mass), original_mass)
            self.assertEqual(dict(self.session.book.energy), original_energy)


    def test_new_book_move_rejects_truncated_history_without_resource_mutation(self):
        """New M01 settlement must fail closed if canonical history was truncated."""
        book = self.session.book
        original_history = book.transaction_history
        seq, mass, energy = book.seq, dict(book.mass), dict(book.energy)
        try:
            book.transaction_history = original_history[:-1]
            with self.assertRaisesRegex(ValueError, 'inconsistent canonical Book transaction history'):
                book.move_once('m01:damaged-history', material=(('plant:forest', 'plant:founder:F001', .001),))
            self.assertNotIn('m01:damaged-history', book.request_receipts)
            self.assertEqual(book.seq, seq)
            self.assertEqual(dict(book.mass), mass)
            self.assertEqual(dict(book.energy), energy)
        finally:
            book.transaction_history = original_history
        book.audit()

    def test_direct_book_replay_rejects_forged_stored_legs(self):
        """A matching request must not replay a canonical receipt with forged stored legs."""
        self.session.harvest('F001', 'replay-legs', 'v1', 'forest', 'plant', .01, .001)
        book = self.session.book
        key = f'm01:{self.tree_id}:replay-legs:v1'
        legs, receipt = book.request_receipts[key]
        forged_material = tuple((s, t, q * .5) for s, t, q in legs[0])
        forged_legs = (forged_material, legs[1])
        self.assertNotEqual(forged_legs, legs)
        seq, mass, energy = book.seq, dict(book.mass), dict(book.energy)
        book.request_receipts[key] = (forged_legs, receipt)
        with self.assertRaisesRegex(ValueError, 'receipt legs do not match canonical Book transaction'):
            book.move_once(key, material=forged_legs[0], energy=forged_legs[1])
        self.assertEqual(book.seq, seq)
        self.assertEqual(dict(book.mass), mass)
        self.assertEqual(dict(book.energy), energy)


    def test_malformed_historical_book_transaction_fails_checkpoint_closed(self):
        """A malformed older transaction must not be accepted with a valid envelope."""
        import pickle
        from dataclasses import replace
        from founders_engine.checkpoint import _encode
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'malformed-history.cp'
            self.session.checkpointed_harvest(
                path, 'F001', 'malformed-history', 'v1',
                'forest', 'plant', .01, .001)
            book = self.session.book
            self.assertGreater(book.seq, 1)
            original = book.transaction_history[0]
            original_seq = book.seq
            mass, energy = dict(book.mass), dict(book.energy)
            try:
                book.transaction_history[0] = replace(original, kind='fabricated')
                path.write_bytes(_encode(pickle.dumps(
                    (self.tree_id, self.world), protocol=pickle.HIGHEST_PROTOCOL)))
                corrupt_bytes = path.read_bytes()
                with self.assertRaisesRegex(ValueError, 'inconsistent canonical Book transaction history'):
                    load_checkpoint(path, self.tree_id)
                with self.assertRaisesRegex(ValueError, 'inconsistent canonical Book transaction history'):
                    save_checkpoint(self.world, self.tree_id, path)
                self.assertEqual(path.read_bytes(), corrupt_bytes)
                self.assertEqual(book.seq, original_seq)
                self.assertEqual(dict(book.mass), mass)
                self.assertEqual(dict(book.energy), energy)
            finally:
                book.transaction_history[0] = original
        book.audit()


    def test_nonfinite_historical_book_leg_fails_checkpoint_closed(self):
        """An older, non-receipted transaction with NaN must fail closed."""
        import pickle
        from dataclasses import replace
        from founders_engine.checkpoint import _encode
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'nonfinite-history.cp'
            self.session.checkpointed_harvest(
                path, 'F001', 'nonfinite-history', 'v1',
                'forest', 'plant', .01, .001)
            book = self.session.book
            original = book.transaction_history[0]
            original_seq = book.seq
            original_mass, original_energy = dict(book.mass), dict(book.energy)
            try:
                # Keep the transaction type and tuple containers valid.
                # This exercises the individual leg validation, not the
                # already-tested kind/container rejection.
                book.transaction_history[0] = replace(
                    original, material=(('plant:a', 'plant:b', float('nan')),))
                path.write_bytes(_encode(pickle.dumps(
                    (self.tree_id, self.world), protocol=pickle.HIGHEST_PROTOCOL)))
                corrupt_bytes = path.read_bytes()
                with self.assertRaisesRegex(ValueError, 'malformed canonical Book transaction leg'):
                    load_checkpoint(path, self.tree_id)
                with self.assertRaisesRegex(ValueError, 'malformed canonical Book transaction leg'):
                    save_checkpoint(self.world, self.tree_id, path)
                self.assertEqual(path.read_bytes(), corrupt_bytes)
                self.assertEqual(book.seq, original_seq)
                self.assertEqual(dict(book.mass), original_mass)
                self.assertEqual(dict(book.energy), original_energy)
            finally:
                book.transaction_history[0] = original
        book.audit()

    def test_book_rejects_whitespace_request_id_before_settlement(self):
        """New Book requests cannot mint replay-key aliases."""
        book = self.session.book
        seq = book.seq
        mass, energy = dict(book.mass), dict(book.energy)
        receipts = dict(book.request_receipts)
        with self.assertRaisesRegex(ValueError, 'nonempty request id required'):
            book.move_once(' alias ', material=(), energy=())
        self.assertEqual(book.seq, seq)
        self.assertEqual(dict(book.mass), mass)
        self.assertEqual(dict(book.energy), energy)
        self.assertEqual(book.request_receipts, receipts)
        book.audit()

    def test_whitespace_alias_of_book_receipt_key_fails_closed(self):
        """A persisted replay ID must not admit whitespace aliases."""
        import pickle
        from founders_engine.checkpoint import _encode
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'whitespace-receipt.cp'
            self.session.checkpointed_harvest(
                path, 'F001', 'whitespace-receipt', 'v1',
                'forest', 'plant', .01, .001)
            book = self.session.book
            original_seq = book.seq
            mass, energy = dict(book.mass), dict(book.energy)
            original_key = f'm01:{self.tree_id}:whitespace-receipt:v1'
            record = book.request_receipts.pop(original_key)
            try:
                book.request_receipts[' ' + original_key] = record
                path.write_bytes(_encode(pickle.dumps(
                    (self.tree_id, self.world), protocol=pickle.HIGHEST_PROTOCOL)))
                corrupted = path.read_bytes()
                with self.assertRaisesRegex(ValueError, 'invalid Book replay request id'):
                    load_checkpoint(path, self.tree_id)
                with self.assertRaisesRegex(ValueError, 'invalid Book replay request id'):
                    save_checkpoint(self.world, self.tree_id, path)
                self.assertEqual(path.read_bytes(), corrupted)
                self.assertEqual(book.seq, original_seq)
                self.assertEqual(dict(book.mass), mass)
                self.assertEqual(dict(book.energy), energy)
            finally:
                book.request_receipts.pop(' ' + original_key, None)
                book.request_receipts[original_key] = record
        book.audit()

    def test_nonfinite_historical_transaction_metadata_fails_closed(self):
        """A checksum-valid checkpoint cannot hide fabricated Book inflow."""
        import pickle
        from dataclasses import replace
        from founders_engine.checkpoint import _encode
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'forged-metadata.cp'
            self.session.checkpointed_harvest(
                path, 'F001', 'metadata-check', 'v1',
                'forest', 'plant', .01, .001)
            book = self.session.book
            original = book.transaction_history[0]
            seq = book.seq
            mass, energy = dict(book.mass), dict(book.energy)
            try:
                for forged in (replace(original, external=float('nan')),
                               replace(original, toll=-1.0)):
                    with self.subTest(forged=repr(forged)):
                        book.transaction_history[0] = forged
                        path.write_bytes(_encode(pickle.dumps(
                            (self.tree_id, self.world),
                            protocol=pickle.HIGHEST_PROTOCOL)))
                        original_bytes = path.read_bytes()
                        with self.assertRaisesRegex(
                                ValueError, 'malformed canonical Book transaction metadata'):
                            load_checkpoint(path, self.tree_id)
                        with self.assertRaisesRegex(
                                ValueError, 'malformed canonical Book transaction metadata'):
                            save_checkpoint(self.world, self.tree_id, path)
                        self.assertEqual(path.read_bytes(), original_bytes)
                        self.assertEqual(book.seq, seq)
                        self.assertEqual(dict(book.mass), mass)
                        self.assertEqual(dict(book.energy), energy)
            finally:
                book.transaction_history[0] = original
        book.audit()


    def test_whitespace_historical_account_fails_closed(self):
        """A checksum-valid checkpoint cannot contain an alias account in history."""
        import pickle
        from dataclasses import replace
        from founders_engine.checkpoint import _encode
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'account-alias.cp'
            self.session.checkpointed_harvest(
                path, 'F001', 'account-alias', 'v1',
                'forest', 'plant', .01, .001)
            book = self.session.book
            original = book.transaction_history[0]
            legs = original.material if original.material else original.energy
            self.assertTrue(legs)
            first = legs[0]
            forged = ((' ' + first[0], first[1], first[2]),) + legs[1:]
            replacement = replace(original, **{
                'material' if original.material else 'energy': forged})
            seq, mass, energy = book.seq, dict(book.mass), dict(book.energy)
            try:
                book.transaction_history[0] = replacement
                path.write_bytes(_encode(pickle.dumps(
                    (self.tree_id, self.world),
                    protocol=pickle.HIGHEST_PROTOCOL)))
                original_bytes = path.read_bytes()
                with self.assertRaisesRegex(ValueError, 'malformed canonical Book transaction leg'):
                    load_checkpoint(path, self.tree_id)
                with self.assertRaisesRegex(ValueError, 'malformed canonical Book transaction leg'):
                    save_checkpoint(self.world, self.tree_id, path)
                self.assertEqual(path.read_bytes(), original_bytes)
                self.assertEqual(book.seq, seq)
                self.assertEqual(dict(book.mass), mass)
                self.assertEqual(dict(book.energy), energy)
            finally:
                book.transaction_history[0] = original
        book.audit()


    def test_boolean_historical_book_sequence_fails_closed(self):
        """True must not alias transaction sequence 1 in a trusted checkpoint."""
        import pickle
        from dataclasses import replace
        from founders_engine.checkpoint import _encode
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'boolean-sequence.cp'
            self.session.checkpointed_harvest(
                path, 'F001', 'bool-sequence', 'v1',
                'forest', 'plant', .01, .001)
            book = self.session.book
            self.assertGreater(book.seq, 1)
            original = book.transaction_history[0]
            self.assertEqual(original.seq, 1)
            seq, mass, energy = book.seq, dict(book.mass), dict(book.energy)
            try:
                book.transaction_history[0] = replace(original, seq=True)
                path.write_bytes(_encode(pickle.dumps(
                    (self.tree_id, self.world),
                    protocol=pickle.HIGHEST_PROTOCOL)))
                forged_bytes = path.read_bytes()
                for action in (lambda: load_checkpoint(path, self.tree_id),
                               lambda: save_checkpoint(self.world, self.tree_id, path)):
                    with self.assertRaisesRegex(
                            ValueError, 'inconsistent canonical Book transaction history'):
                        action()
                self.assertEqual(path.read_bytes(), forged_bytes)
                self.assertEqual(book.seq, seq)
                self.assertEqual(dict(book.mass), mass)
                self.assertEqual(dict(book.energy), energy)
            finally:
                book.transaction_history[0] = original
        book.audit()


    def test_boolean_replay_receipt_sequence_fails_closed(self):
        """A replay receipt with seq=True must not impersonate canonical seq=1."""
        import pickle
        from dataclasses import replace
        from founders_engine.checkpoint import _encode
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'boolean-receipt.cp'
            self.session.checkpointed_harvest(
                path, 'F001', 'bool-receipt', 'v1',
                'forest', 'plant', .01, .001)
            book = self.session.book
            key = f'm01:{self.tree_id}:bool-receipt:v1'
            legs, receipt = book.request_receipts[key]
            original = book.request_receipts[key]
            seq, mass, energy = book.seq, dict(book.mass), dict(book.energy)
            try:
                book.request_receipts[key] = (legs, replace(receipt, seq=True))
                path.write_bytes(_encode(pickle.dumps(
                    (self.tree_id, self.world),
                    protocol=pickle.HIGHEST_PROTOCOL)))
                forged_bytes = path.read_bytes()
                for action in (lambda: load_checkpoint(path, self.tree_id),
                               lambda: save_checkpoint(self.world, self.tree_id, path)):
                    with self.assertRaisesRegex(ValueError, 'inconsistent Book replay receipt'):
                        action()
                self.assertEqual(path.read_bytes(), forged_bytes)
                self.assertEqual(book.seq, seq)
                self.assertEqual(dict(book.mass), mass)
                self.assertEqual(dict(book.energy), energy)
            finally:
                book.request_receipts[key] = original
        book.audit()

if __name__ == '__main__':
    unittest.main()
