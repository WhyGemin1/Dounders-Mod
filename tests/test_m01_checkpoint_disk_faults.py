"""Real Core151 M01 disk-boundary fault injection; no native WorldBox writes.

Faults are injected into the actual checkpoint writer (not a mocked writer).
After a failed save the RAM session is unusable; recovery must examine the
durable Book receipt, not assume that a failed call means no settlement.
"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from founders_engine.checkpoint import load_checkpoint, save_checkpoint
from run_world_tree_pilot import bootstrap
from founders_engine.authority import SingleEngineSession
import founders_engine.checkpoint as checkpoint


class AtomicCheckpointFaultTests(unittest.TestCase):
    def setUp(self):
        self.world, _, self.tree_id = bootstrap(400)
        self.session = SingleEngineSession(self.world, self.tree_id)

    def _exercise(self, failure_stage, expected_settled):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'world.cp'
            save_checkpoint(self.world, self.tree_id, path)
            original_bytes = path.read_bytes()
            before = self.session.book.seq
            original_fsync = checkpoint.os.fsync
            original_replace = checkpoint.os.replace
            fsync_calls = [0]

            def fault_fsync(fd):
                fsync_calls[0] += 1
                if failure_stage == 'file_fsync' and fsync_calls[0] == 1:
                    raise OSError('injected file fsync failure')
                if failure_stage == 'directory_fsync' and fsync_calls[0] == 2:
                    raise OSError('injected directory fsync failure')
                return original_fsync(fd)

            def fault_replace(source, destination):
                if failure_stage == 'replace':
                    raise OSError('injected atomic replace failure')
                return original_replace(source, destination)

            with patch.object(checkpoint.os, 'fsync', side_effect=fault_fsync), \
                 patch.object(checkpoint.os, 'replace', side_effect=fault_replace):
                with self.assertRaisesRegex(OSError, 'injected'):
                    self.session.checkpointed_harvest(
                        path, 'F001', 'fault-lot', 'v1',
                        'forest', 'plant', .01, .001)

            # The in-memory Book settled, but may not be durable.
            self.assertEqual(self.session.book.seq, before + 1)
            with self.assertRaisesRegex(RuntimeError, 'reload durable world'):
                self.session.step()
            with self.assertRaisesRegex(RuntimeError, 'reload durable world'):
                self.session.harvest('F002', 'after-fault', 'v1',
                                     'forest', 'plant', .01)

            recovered = load_checkpoint(path, self.tree_id)
            receipt_key = f'm01:{self.tree_id}:fault-lot:v1'
            self.assertEqual(receipt_key in recovered.book.request_receipts,
                             expected_settled)
            self.assertEqual(recovered.book.seq, before + int(expected_settled))
            if not expected_settled:
                self.assertEqual(path.read_bytes(), original_bytes)

            # The SAME request ID is safe to replay regardless of whether the
            # replacement reached disk. No duplicate settlement is possible.
            recovered.checkpointed_harvest(
                path, 'F001', 'fault-lot', 'v1',
                'forest', 'plant', .01, .001)
            self.assertEqual(recovered.book.seq, before + 1)
            again = load_checkpoint(path, self.tree_id)
            self.assertEqual(again.book.seq, before + 1)
            self.assertEqual(len(again.book.request_receipts), 1)
            self.assertEqual(dict(again.book.mass), dict(recovered.book.mass))
            self.assertEqual(dict(again.book.energy), dict(recovered.book.energy))
            self.assertEqual(again.world.tick, self.world.tick)
            self.assertEqual(len(again.world.founders.people), 100)
            self.assertIs(again.world.founders.book, again.book)
            self.assertIs(again.world.world_trees.worlds[self.tree_id].book,
                          again.book)
            again.audit()

    def test_file_fsync_failure_keeps_previous_checkpoint(self):
        self._exercise('file_fsync', False)

    def test_atomic_replace_failure_keeps_previous_checkpoint(self):
        self._exercise('replace', False)

    def test_directory_fsync_failure_reloads_replaced_checkpoint(self):
        # os.replace already succeeded before the injected directory fsync
        # failure. This is only a simulated process-level failure, not proof
        # that a real power loss would preserve the new directory entry.
        self._exercise('directory_fsync', True)


if __name__ == '__main__':
    unittest.main()
