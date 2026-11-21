"""C086 fail-closed native checkpoint validation; no game mutation."""
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "bridge" / "native_identity_gate.py"
spec = importlib.util.spec_from_file_location("native_identity_gate", SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def evidence():
    snap = {"paused": True, "world_loading": False, "has_more": False,
            "offset": 0, "missing_identity_count": 0, "duplicate_identity_count": 0,
            "returned": 2, "matched": 2, "world_seed": 42,
            "items": [{"native_actor_id": "A", "asset_id": "wolf"},
                      {"native_actor_id": "B", "asset_id": "rabbit"}]}
    def event(seq, actor, data):
        return {"kind": "nutrition_call", "seq": seq, "session_id": "s1",
                "world_key": "world1", "native_success": True,
                "actor_id": actor, "actor_data_id": data}
    return snap, event


class CheckpointMappingTests(unittest.TestCase):
    def test_valid_continuation_and_deterministic_replay(self):
        snap, event = evidence()
        first = mod.reconcile_epoch(snap, [event(1, 10, "A")])
        next_events = [event(2, 20, "B")]
        result = mod.reconcile_epoch(snap, next_events, first)
        self.assertEqual(result["mapping"], {"10": "A", "20": "B"})
        self.assertEqual(result["last_seq"], 2)
        self.assertEqual(result, mod.reconcile_epoch(snap, next_events, first))

    def test_checkpoint_alias_rejected(self):
        snap, event = evidence()
        checkpoint = mod.reconcile_epoch(snap, [event(1, 10, "A")])
        checkpoint["mapping"]["20"] = "A"
        with self.assertRaisesRegex(ValueError, "non-injective"):
            mod.reconcile_epoch(snap, [event(2, 30, "B")], checkpoint)

    def test_checkpoint_blank_key_rejected(self):
        snap, event = evidence()
        checkpoint = mod.reconcile_epoch(snap, [event(1, 10, "A")])
        checkpoint["mapping"][""] = "B"
        with self.assertRaisesRegex(ValueError, "invalid checkpoint"):
            mod.reconcile_epoch(snap, [event(2, 30, "B")], checkpoint)

    def test_checkpoint_noncanonical_value_rejected(self):
        snap, event = evidence()
        checkpoint = mod.reconcile_epoch(snap, [event(1, 10, "A")])
        checkpoint["mapping"]["10"] = " A "
        with self.assertRaisesRegex(ValueError, "noncanonical|checkpoint actor absent from M01 snapshot"):
            mod.reconcile_epoch(snap, [event(2, 30, "B")], checkpoint)

    def test_checkpoint_non_string_value_rejected(self):
        snap, event = evidence()
        checkpoint = mod.reconcile_epoch(snap, [event(1, 10, "A")])
        checkpoint["mapping"]["10"] = 123
        with self.assertRaisesRegex(ValueError, "invalid checkpoint"):
            mod.reconcile_epoch(snap, [event(2, 30, "B")], checkpoint)

    def test_replayed_batch_rejected(self):
        snap, event = evidence()
        checkpoint = mod.reconcile_epoch(snap, [event(1, 10, "A")])
        with self.assertRaisesRegex(ValueError, "replayed or skipped"):
            mod.reconcile_epoch(snap, [event(1, 20, "B")], checkpoint)


if __name__ == "__main__":
    unittest.main()
