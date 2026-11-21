"""Actual subprocess termination at Core151 checkpoint write boundaries.

Child processes terminate with os._exit(73), bypassing exception handlers.
These are process-exit tests on a normal filesystem, NOT power-loss tests.
Only one IntegratedWorld/Book exists per process; no native WorldBox writes.
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from founders_engine.checkpoint import load_checkpoint, save_checkpoint
from founders_engine.authority import SingleEngineSession
from run_world_tree_pilot import bootstrap

_CHILD = r"""
import os
import sys
from pathlib import Path
from founders_engine.checkpoint import load_checkpoint
import founders_engine.checkpoint as cp

path = Path(sys.argv[1])
stage = sys.argv[2]
session = load_checkpoint(path)
if stage == 'before_replace':
    original = cp.os.replace
    def terminate(src, dst):
        os._exit(73)
    cp.os.replace = terminate
elif stage == 'after_replace':
    original = cp.os.replace
    def terminate(src, dst):
        original(src, dst)
        os._exit(73)
    cp.os.replace = terminate
else:
    raise ValueError('unsupported kill point')
session.checkpointed_harvest(
    path, 'F001', 'process-kill-lot', 'v1', 'forest', 'plant', .01, .001)
raise AssertionError('child should have terminated during checkpoint')
"""


class ProcessTerminationTests(unittest.TestCase):
    def _exercise(self, stage, expected_settled):
        world, _, tree_id = bootstrap(400)
        session = SingleEngineSession(world, tree_id)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'world.cp'
            save_checkpoint(world, tree_id, path)
            initial_bytes = path.read_bytes()
            seq = session.book.seq
            before_mass = dict(session.book.mass)
            before_energy = dict(session.book.energy)

            # A fresh interpreter restores the REAL checkpoint and terminates
            # itself at the selected actual os.replace boundary.
            child = subprocess.run(
                [sys.executable, '-c', _CHILD, str(path), stage],
                cwd=str(Path(__file__).resolve().parent.parent),
                capture_output=True, text=True, timeout=60,
                env=dict(os.environ, PYTHONPATH=str(
                    Path(__file__).resolve().parent.parent / 'src')))
            self.assertEqual(child.returncode, 73,
                             f'subprocess failed: {child.stderr}')
            restored = load_checkpoint(path, tree_id)
            request_id = f'm01:{tree_id}:process-kill-lot:v1'
            self.assertEqual(request_id in restored.book.request_receipts,
                             expected_settled)
            self.assertEqual(restored.book.seq, seq + int(expected_settled))
            self.assertEqual(restored.world.tick, world.tick)
            self.assertEqual(len(restored.world.founders.people), 100)
            self.assertIs(restored.world.founders.book, restored.book)
            self.assertIs(restored.world.world_trees.worlds[tree_id].book,
                          restored.book)
            if not expected_settled:
                self.assertEqual(path.read_bytes(), initial_bytes)
                self.assertEqual(dict(restored.book.mass), before_mass)
                self.assertEqual(dict(restored.book.energy), before_energy)

            # Recovery inspects the Book receipt, then retries the SAME
            # request. A settled claim must not transfer twice.
            restored.checkpointed_harvest(
                path, 'F001', 'process-kill-lot', 'v1',
                'forest', 'plant', .01, .001)
            self.assertEqual(restored.book.seq, seq + 1)
            final = load_checkpoint(path, tree_id)
            self.assertEqual(final.book.seq, seq + 1)
            self.assertEqual(len(final.book.request_receipts), 1)
            self.assertEqual(dict(final.book.mass), dict(restored.book.mass))
            self.assertEqual(dict(final.book.energy), dict(restored.book.energy))
            final.audit()

    def test_process_exit_before_atomic_replace(self):
        self._exercise('before_replace', False)

    def test_process_exit_after_atomic_replace(self):
        self._exercise('after_replace', True)


if __name__ == '__main__':
    unittest.main()
