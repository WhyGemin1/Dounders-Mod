"""M01: compare one live Core151 world with checkpoint-restarted execution.

Both arms run the ACTUAL IntegratedWorld, not shadow ecological simulators.
The only harvesting performed is synthetic Book-funded Tree inventory transfer.
No WorldBox native game integration or external ACK is asserted.
"""
import tempfile
import unittest
from pathlib import Path

from founders_engine.authority import SingleEngineSession
from founders_engine.checkpoint import load_checkpoint, save_checkpoint
from run_world_tree_pilot import bootstrap


def _prove_authority(session):
    world = session.world
    assert world.book is session.book
    assert world.founders.book is session.book
    assert world.tick == world.ecology.day
    assert len(world.founders.people) == 100
    for tree in world.world_trees.worlds.values():
        assert tree.book is session.book
        assert tree.sim is world
    return session.book.audit()


class MultiTickCheckpointTests(unittest.TestCase):
    def test_three_ticks_with_harvest_before_and_after_restart(self):
        original, _, tree_id = bootstrap(400)
        live = SingleEngineSession(original, tree_id)

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'single-world.cp'
            save_checkpoint(live.world, tree_id, path)
            restarted = load_checkpoint(path, expected_tree_id=tree_id)
            initial_tick = live.world.tick

            # Claim one existing Tree food lot in both execution arms.
            initial_live = live.harvest('F001', 'matched-lot-1', 'v1',
                                        'forest', 'plant', .01, .001)
            initial_restarted = restarted.harvest('F001', 'matched-lot-1', 'v1',
                                                  'forest', 'plant', .01, .001)
            self.assertEqual(initial_live, initial_restarted)
            pre_tick_seq = live.book.seq
            self.assertEqual(restarted.book.seq, pre_tick_seq)

            for offset in range(3):
                # A second claim occurs AFTER the restored arm was reopened.
                if offset == 1:
                    second_live = live.harvest('F002', 'matched-lot-2', 'v1',
                                               'wetland', 'plant', .01, .001)
                    second_restarted = restarted.harvest(
                        'F002', 'matched-lot-2', 'v1',
                        'wetland', 'plant', .01, .001)
                    self.assertEqual(second_live, second_restarted)

                live.step()
                restarted.step()

                # The repeated transfer must not mint resources or Book entries.
                before_live = live.book.seq
                before_restarted = restarted.book.seq
                self.assertEqual(
                    live.harvest('F001', 'matched-lot-1', 'v1',
                                 'forest', 'plant', .01, .001),
                    initial_live)
                self.assertEqual(
                    restarted.harvest('F001', 'matched-lot-1', 'v1',
                                      'forest', 'plant', .01, .001),
                    initial_restarted)
                self.assertEqual(live.book.seq, before_live)
                self.assertEqual(restarted.book.seq, before_restarted)

                # Book integrity, Founder identity and ecological clock on EACH day.
                _prove_authority(live)
                _prove_authority(restarted)
                self.assertEqual(live.world.tick, initial_tick + offset + 1)
                self.assertEqual(live.world.tick, restarted.world.tick)

                # Compare semantic physical/accounting/ecological state,
                # never raw pickle bytes.
                self.assertEqual(live.book.seq, restarted.book.seq)
                self.assertEqual(dict(live.book.mass), dict(restarted.book.mass))
                self.assertEqual(dict(live.book.energy), dict(restarted.book.energy))
                self.assertEqual(live.book.request_receipts,
                                 restarted.book.request_receipts)
                self.assertEqual(set(live.world.founders.people),
                                 set(restarted.world.founders.people))
                self.assertEqual(live.world.ecology.counter,
                                 restarted.world.ecology.counter)
                self.assertEqual(live.world.world_trees.worlds[tree_id].residents,
                                 restarted.world.world_trees.worlds[tree_id].residents)
                self.assertEqual(live.world.seeds.plants,
                                 restarted.world.seeds.plants)

                # Restart ONLY one arm; the other stays uninterrupted in memory.
                save_checkpoint(restarted.world, tree_id, path)
                restarted = load_checkpoint(path, expected_tree_id=tree_id)

            # After the third restart, both claims are still exactly-once.
            self.assertEqual(len(live.book.request_receipts), 2)
            self.assertEqual(len(restarted.book.request_receipts), 2)
            self.assertEqual(live.book.seq, restarted.book.seq)
            self.assertEqual(live.world.tick, initial_tick + 3)
            self.assertEqual(live.world.events, restarted.world.events)

    def test_changed_request_after_checkpoint_is_rejected_without_mutation(self):
        world, _, tree_id = bootstrap(400)
        live = SingleEngineSession(world, tree_id)
        live.harvest('F001', 'immutable-lot', 'v1', 'forest', 'plant', .01)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'single-world.cp'
            save_checkpoint(world, tree_id, path)
            restarted = load_checkpoint(path, expected_tree_id=tree_id)
            seq = restarted.book.seq
            before = (dict(restarted.book.mass), dict(restarted.book.energy))
            with self.assertRaisesRegex(ValueError, 'different transfer'):
                restarted.harvest('F001', 'immutable-lot', 'v1',
                                  'forest', 'plant', .02)
            self.assertEqual(restarted.book.seq, seq)
            self.assertEqual(
                (dict(restarted.book.mass), dict(restarted.book.energy)), before)
            _prove_authority(restarted)


if __name__ == '__main__':
    unittest.main()
