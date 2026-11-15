"""Real child-process exits at Core151 checkpoint fsync boundaries.

os._exit bypasses Python cleanup, but these are NOT power-loss simulations.
Every recovery loads the original IntegratedWorld and its sole Book.
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from founders_engine.authority import SingleEngineSession
from founders_engine.checkpoint import load_checkpoint, save_checkpoint
from run_world_tree_pilot import bootstrap

_CHILD = r"""
import os
import stat
import sys
from pathlib import Path
from founders_engine.checkpoint import load_checkpoint
import founders_engine.checkpoint as cp

path = Path(sys.argv[1])
stage = sys.argv[2]
session = load_checkpoint(path)
original = cp.os.fsync

def terminate(fd):
    directory = stat.S_ISDIR(os.fstat(fd).st_mode)
    target = ('directory' if directory else 'file')
    before = stage == target + '_before'
    after = stage == target + '_after'
    if before:
        os._exit(73)
    original(fd)
    if after:
        os._exit(73)

cp.os.fsync = terminate
session.checkpointed_harvest(
    path, 'F001', 'fsync-kill-lot', 'v1', 'forest', 'plant', .01, .001)
raise AssertionError('child did not exit at the selected fsync boundary')
"""


class FsyncProcessTerminationTests(unittest.TestCase):
    def _exercise(self, stage, expected_settled):
        world, _, tree_id = bootstrap(400)
        session = SingleEngineSession(world, tree_id)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'world.cp'
            save_checkpoint(world, tree_id, path)
            previous_bytes = path.read_bytes()
            previous_seq = session.book.seq
            previous_mass = dict(session.book.mass)
            previous_energy = dict(session.book.energy)

            child = subprocess.run(
                [sys.executable, '-c', _CHILD, str(path), stage],
                cwd=str(Path(__file__).resolve().parent.parent),
                capture_output=True, text=True, timeout=60,
                env=dict(os.environ, PYTHONPATH=str(
                    Path(__file__).resolve().parent.parent / 'src')))
            self.assertEqual(child.returncode, 73,
                             f'child failed at {stage}: {child.stderr}')

            restored = load_checkpoint(path, tree_id)
            request_id = f'm01:{tree_id}:fsync-kill-lot:v1'
            self.assertEqual(request_id in restored.book.request_receipts,
                             expected_settled)
            self.assertEqual(restored.book.seq,
                             previous_seq + int(expected_settled))
            self.assertEqual(restored.world.tick, world.tick)
            self.assertEqual(len(restored.world.founders.people), 100)
            self.assertIs(restored.world.founders.book, restored.book)
            self.assertIs(restored.world.world_trees.worlds[tree_id].book,
                          restored.book)
            if not expected_settled:
                self.assertEqual(path.read_bytes(), previous_bytes)
                self.assertEqual(dict(restored.book.mass), previous_mass)
                self.assertEqual(dict(restored.book.energy), previous_energy)

            restored.checkpointed_harvest(
                path, 'F001', 'fsync-kill-lot', 'v1',
                'forest', 'plant', .01, .001)
            self.assertEqual(restored.book.seq, previous_seq + 1)
            final = load_checkpoint(path, tree_id)
            self.assertEqual(final.book.seq, previous_seq + 1)
            self.assertEqual(len(final.book.request_receipts), 1)
            self.assertEqual(dict(final.book.mass), dict(restored.book.mass))
            self.assertEqual(dict(final.book.energy), dict(restored.book.energy))
            final.audit()

    def test_exit_before_temporary_file_fsync(self):
        self._exercise('file_before', False)

    def test_exit_after_temporary_file_fsync(self):
        self._exercise('file_after', False)

    def test_exit_before_directory_fsync(self):
        self._exercise('directory_before', True)

    def test_exit_after_directory_fsync(self):
        self._exercise('directory_after', True)


if __name__ == '__main__':
    unittest.main()
