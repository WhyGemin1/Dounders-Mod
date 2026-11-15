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


if __name__ == '__main__':
    unittest.main()
