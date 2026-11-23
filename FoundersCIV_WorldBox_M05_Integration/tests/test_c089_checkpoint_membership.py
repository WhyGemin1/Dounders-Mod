"""C089 checkpoint membership and canonical callback regression tests."""
import importlib.util
import pathlib
import unittest

MODULE = pathlib.Path(__file__).resolve().parents[1] / "bridge" / "native_identity_gate.py"
spec = importlib.util.spec_from_file_location("native_identity_gate", MODULE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

def snapshot():
    return dict(paused=True, world_loading=False, has_more=False, offset=0,
                missing_identity_count=0, duplicate_identity_count=0,
                returned=1, matched=1, world_seed=42,
                items=[dict(native_actor_id="native-1", asset_id="human")])

def event(seq):
    return dict(seq=seq, session_id="session-A", world_key="world-A",
                kind="nutrition_call", native_success=True,
                actor_id=7, actor_data_id="native-1")

def checkpoint(mapping):
    return dict(schema=1, world_seed=42, world_key="world-A",
                session_id="session-A", mapping=mapping, last_seq=1)

class CheckpointMembershipTests(unittest.TestCase):
    def test_valid_continuation(self):
        result = gate.reconcile_epoch(snapshot(), [event(2)], checkpoint({"7":"native-1"}))
        self.assertEqual(result["last_seq"], 2)
        self.assertEqual(result["mapping"], {"7":"native-1"})

    def test_stale_native_identity_rejected(self):
        with self.assertRaisesRegex(ValueError, "absent"):
            gate.reconcile_epoch(snapshot(), [event(2)], checkpoint({"8":"missing-native"}))

    def test_leading_zero_callback_alias_rejected(self):
        with self.assertRaisesRegex(ValueError, "noncanonical callback"):
            gate.reconcile_epoch(snapshot(), [event(2)], checkpoint({"07":"native-1"}))

    def test_non_ascii_digit_callback_rejected(self):
        with self.assertRaisesRegex(ValueError, "noncanonical callback"):
            gate.reconcile_epoch(snapshot(), [event(2)], checkpoint({"٧":"native-1"}))

    def test_snapshot_membership_is_read_only(self):
        snap = snapshot()
        original = repr(snap)
        gate.reconcile_epoch(snap, [event(2)], checkpoint({"7":"native-1"}))
        self.assertEqual(repr(snap), original)

if __name__ == "__main__":
    unittest.main()
