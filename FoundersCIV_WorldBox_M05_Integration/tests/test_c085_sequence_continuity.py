"""C085 regression: cross-batch sequence replay safety, read-only native events."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bridge"))
from native_identity_gate import reconcile_epoch

def snapshot():
    return dict(paused=True, world_loading=False, has_more=False, offset=0,
                missing_identity_count=0, duplicate_identity_count=0,
                returned=1, matched=1, world_seed=91,
                items=[dict(native_actor_id="actor-1", asset_id="rabbit")])

def event(seq):
    return dict(seq=seq, kind="nutrition_call", native_success=True,
                session_id="s1", world_key="world-1", actor_id=7,
                actor_data_id="actor-1")

class SequenceContinuity(unittest.TestCase):
    def test_next_batch_advances(self):
        first = reconcile_epoch(snapshot(), [event(1), event(2)])
        self.assertEqual(first["last_seq"], 2)
        second = reconcile_epoch(snapshot(), [event(3)], first)
        self.assertEqual(second["last_seq"], 3)
        self.assertEqual(second["mapping"], first["mapping"])

    def test_replay_rejected(self):
        first = reconcile_epoch(snapshot(), [event(1), event(2)])
        with self.assertRaises(ValueError):
            reconcile_epoch(snapshot(), [event(2)], first)

    def test_gap_rejected(self):
        first = reconcile_epoch(snapshot(), [event(1), event(2)])
        with self.assertRaises(ValueError):
            reconcile_epoch(snapshot(), [event(4)], first)

    def test_legacy_checkpoint_fails_closed(self):
        first = reconcile_epoch(snapshot(), [event(1)])
        first.pop("last_seq")
        with self.assertRaises(ValueError):
            reconcile_epoch(snapshot(), [event(2)], first)

    def test_boolean_sequence_rejected(self):
        first = reconcile_epoch(snapshot(), [event(1)])
        first["last_seq"] = True
        with self.assertRaises(ValueError):
            reconcile_epoch(snapshot(), [event(2)], first)

if __name__ == "__main__":
    unittest.main()
