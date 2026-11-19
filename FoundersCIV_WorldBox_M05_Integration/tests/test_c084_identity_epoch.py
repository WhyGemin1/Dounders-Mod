"""C084 synthetic epoch continuity tests. Not a live WorldBox test."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bridge"))
from native_identity_gate import reconcile_epoch


def snapshot(seed=42):
    return {"paused": True, "world_loading": False, "has_more": False,
            "offset": 0, "missing_identity_count": 0,
            "duplicate_identity_count": 0, "world_seed": seed,
            "items": [{"native_actor_id": "native-A", "asset_id": "rabbit"}],
            "returned": 1, "matched": 1}


def events(callback=17, native="native-A", session="session-1", world="world-1"):
    return [{"seq": 1, "session_id": session, "world_key": world,
             "kind": "nutrition_call", "native_success": True,
             "actor_id": callback, "actor_data_id": native}]


class EpochTests(unittest.TestCase):
    def test_valid_epoch(self):
        c = reconcile_epoch(snapshot(), events())
        self.assertEqual(c["mapping"], {"17": "native-A"})

    def test_checkpoint_replay_idempotent(self):
        c = reconcile_epoch(snapshot(), events())
        self.assertEqual(reconcile_epoch(snapshot(), events(), c), c)

    def test_changed_seed_fails_closed(self):
        c = reconcile_epoch(snapshot(), events())
        with self.assertRaises(ValueError):
            reconcile_epoch(snapshot(43), events(), c)

    def test_changed_session_fails_closed(self):
        c = reconcile_epoch(snapshot(), events())
        with self.assertRaises(ValueError):
            reconcile_epoch(snapshot(), events(session="session-2"), c)

    def test_changed_world_fails_closed(self):
        c = reconcile_epoch(snapshot(), events())
        with self.assertRaises(ValueError):
            reconcile_epoch(snapshot(), events(world="world-2"), c)

    def test_callback_reassignment_fails_closed(self):
        c = reconcile_epoch(snapshot(), events())
        with self.assertRaises(ValueError):
            reconcile_epoch(snapshot(), events(callback=18), c)

    def test_malformed_checkpoint_fails_closed(self):
        with self.assertRaises(ValueError):
            reconcile_epoch(snapshot(), events(), {"schema": 2})

    def test_explicit_new_epoch_allowed(self):
        self.assertEqual(reconcile_epoch(snapshot(43), events(session="new"))["world_seed"], 43)

    def test_no_events_cannot_certify_epoch(self):
        with self.assertRaises(ValueError):
            reconcile_epoch(snapshot(), [])

    def test_no_mutation_of_input_checkpoint(self):
        c = reconcile_epoch(snapshot(), events())
        before = dict(c["mapping"])
        reconcile_epoch(snapshot(), events(), c)
        self.assertEqual(c["mapping"], before)


if __name__ == "__main__":
    unittest.main()
