"""C088 strict native evidence types; run: python -m unittest discover -s FoundersCIV_WorldBox_M05_Integration/tests -p 'test_c088*.py'."""
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "bridge" / "native_identity_gate.py"
spec = importlib.util.spec_from_file_location("c088_gate", SOURCE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def snapshot():
    return dict(paused=True, world_loading=False, has_more=False, offset=0,
                missing_identity_count=0, duplicate_identity_count=0,
                world_seed=42, returned=1, matched=1,
                items=[dict(native_actor_id="native-1", asset_id="rabbit")])


def event():
    return dict(seq=1, kind="nutrition_call", native_success=True,
                session_id="session-1", world_key="world-1",
                actor_id=17, actor_data_id="native-1")


class StrictNativeEvidenceTypes(unittest.TestCase):
    def test_valid_evidence_maps_actor(self):
        self.assertEqual(gate.reconcile(snapshot(), [event()]), {"17": "native-1"})

    def test_boolean_returned_count_rejected(self):
        s = snapshot(); s["returned"] = True
        with self.assertRaises(ValueError): gate.reconcile(s, [event()])

    def test_boolean_matched_count_rejected(self):
        s = snapshot(); s["matched"] = True
        with self.assertRaises(ValueError): gate.reconcile(s, [event()])

    def test_boolean_world_seed_rejected(self):
        s = snapshot(); s["world_seed"] = True
        with self.assertRaises(ValueError): gate.reconcile(s, [event()])

    def test_boolean_session_rejected(self):
        e = event(); e["session_id"] = True
        with self.assertRaises(ValueError): gate.reconcile(snapshot(), [e])

    def test_numeric_world_key_rejected(self):
        e = event(); e["world_key"] = 1
        with self.assertRaises(ValueError): gate.reconcile(snapshot(), [e])

    def test_whitespace_session_rejected(self):
        e = event(); e["session_id"] = " session-1 "
        with self.assertRaises(ValueError): gate.reconcile(snapshot(), [e])

    def test_whitespace_world_key_rejected(self):
        e = event(); e["world_key"] = " world-1 "
        with self.assertRaises(ValueError): gate.reconcile(snapshot(), [e])

    def test_valid_epoch_checkpoint(self):
        cp = gate.reconcile_epoch(snapshot(), [event()])
        e = event(); e["seq"] = 2
        self.assertEqual(gate.reconcile_epoch(snapshot(), [e], cp)["last_seq"], 2)

    def test_boolean_checkpoint_schema_rejected(self):
        cp = gate.reconcile_epoch(snapshot(), [event()])
        cp["schema"] = True
        e = event(); e["seq"] = 2
        with self.assertRaises(ValueError): gate.reconcile_epoch(snapshot(), [e], cp)


if __name__ == "__main__":
    unittest.main()
