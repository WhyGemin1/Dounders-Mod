"""Trusted-local durable voluntary stewardship on the one Core151 Book."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from founders_engine.authority import SingleEngineSession
from founders_engine.checkpoint import load_checkpoint, save_checkpoint
from run_world_tree_pilot import bootstrap


class CheckpointedTendingTests(unittest.TestCase):
    def test_successful_tending_persists_once_across_restart(self):
        world, _, tree_id = bootstrap(451)
        session = SingleEngineSession(world, tree_id)
        founder = next(iter(world.founders.people))
        account = f'founder:{founder}'
        reserve = f'reserve:{tree_id}'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'world.cp'
            save_checkpoint(world, tree_id, path)
            before = (world.book.seq, world.book.energy[account],
                      world.book.energy[reserve], world.tick)
            session.checkpointed_tend_tree(path, founder, tree_id, .01)
            after = (world.book.seq, world.book.energy[account],
                     world.book.energy[reserve], world.tick)
            self.assertGreater(after[0], before[0])
            self.assertAlmostEqual(after[1], before[1] - .01, places=6)
            self.assertAlmostEqual(after[2], before[2] + .01, places=6)
            self.assertEqual(after[3], before[3])
            restored = load_checkpoint(path, expected_tree_id=tree_id)
            self.assertEqual(
                (restored.book.seq, restored.book.energy[account],
                 restored.book.energy[reserve], restored.world.tick), after)
            self.assertEqual(restored.audit().founder_count, 100)

    def test_failed_save_quarantines_and_restores_prior_checkpoint(self):
        world, _, tree_id = bootstrap(452)
        session = SingleEngineSession(world, tree_id)
        founder = next(iter(world.founders.people))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'world.cp'
            save_checkpoint(world, tree_id, path)
            before = load_checkpoint(path, expected_tree_id=tree_id)
            with patch('founders_engine.checkpoint.save_checkpoint',
                       side_effect=OSError('injected disk failure')):
                with self.assertRaises(OSError):
                    session.checkpointed_tend_tree(path, founder, tree_id, .01)
            with self.assertRaisesRegex(RuntimeError, 'checkpoint outcome uncertain'):
                session.audit()
            restored = load_checkpoint(path, expected_tree_id=tree_id)
            self.assertEqual(restored.book.seq, before.book.seq)
            self.assertEqual(restored.world.tick, before.world.tick)
            self.assertEqual(restored.book.energy, before.book.energy)
            self.assertLessEqual(abs(restored.audit().book_energy_error), 1e-6)


if __name__ == '__main__':
    unittest.main()
