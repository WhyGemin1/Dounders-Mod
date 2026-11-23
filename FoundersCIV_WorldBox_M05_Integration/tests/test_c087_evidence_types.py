"""C087 negative controls for native actor evidence type-confusion.

Synthetic fixtures only. No native WorldBox or ecological assertions.
"""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bridge"))
from native_identity_gate import reconcile, reconcile_epoch


def evidence():
    snapshot = dict(paused=True, world_loading=False, has_more=False, offset=0,
                    missing_identity_count=0, duplicate_identity_count=0,
                    world_seed=42, matched=1, returned=1,
                    items=[dict(native_actor_id="A", asset_id="rabbit")])
    event = dict(seq=1, session_id="S", world_key="W",
                 kind="nutrition_call", native_success=True,
                 actor_id=17, actor_data_id="A")
    return snapshot, [event]


class EvidenceTypeSafety(unittest.TestCase):
    def test_valid_control_and_checkpoint(self):
        s, e = evidence()
        self.assertEqual(reconcile(s, e), {"17": "A"})
        self.assertEqual(reconcile_epoch(s, e)["mapping"], {"17": "A"})

    def test_boolean_snapshot_offset_rejected(self):
        s, e = evidence()
        s["offset"] = False
        with self.assertRaisesRegex(ValueError, "incomplete"):
            reconcile(s, e)

    def test_integer_snapshot_paused_rejected(self):
        s, e = evidence()
        s["paused"] = 1
        with self.assertRaisesRegex(ValueError, "incomplete"):
            reconcile(s, e)

    def test_boolean_snapshot_count_rejected(self):
        s, e = evidence()
        s["missing_identity_count"] = False
        with self.assertRaisesRegex(ValueError, "incomplete"):
            reconcile(s, e)

    def test_numeric_native_id_rejected(self):
        s, e = evidence()
        s["items"][0]["native_actor_id"] = 123
        with self.assertRaisesRegex(ValueError, "invalid native"):
            reconcile(s, e)

    def test_whitespace_native_id_rejected(self):
        s, e = evidence()
        s["items"][0]["native_actor_id"] = " A "
        with self.assertRaisesRegex(ValueError, "invalid native"):
            reconcile(s, e)

    def test_boolean_callback_id_rejected(self):
        s, e = evidence()
        e[0]["actor_id"] = True
        with self.assertRaisesRegex(ValueError, "unresolved"):
            reconcile(s, e)

    def test_string_callback_id_rejected(self):
        s, e = evidence()
        e[0]["actor_id"] = "17"
        with self.assertRaisesRegex(ValueError, "unresolved"):
            reconcile(s, e)

    def test_noncanonical_event_data_id_rejected(self):
        s, e = evidence()
        e[0]["actor_data_id"] = " A "
        with self.assertRaisesRegex(ValueError, "unresolved"):
            reconcile(s, e)

    def test_no_mutation_on_rejected_event(self):
        s, e = evidence()
        e[0]["actor_id"] = True
        original = dict(s)
        with self.assertRaises(ValueError):
            reconcile(s, e)
        self.assertEqual(s, original)


if __name__ == "__main__":
    unittest.main()
