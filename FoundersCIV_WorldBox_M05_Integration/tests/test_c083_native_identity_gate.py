import unittest
from native_identity_gate import reconcile

def fixture():
    snapshot = dict(paused=True, world_loading=False, has_more=False, offset=0,
                    missing_identity_count=0, duplicate_identity_count=0,
                    world_seed=9711, matched=2, returned=2,
                    items=[dict(native_actor_id="101",asset_id="rabbit"),
                           dict(native_actor_id="102",asset_id="rabbit")])
    events = [dict(seq=1,session_id="S",world_key="W",kind="nutrition_call",
                   native_success=True,actor_id=501,actor_data_id="101")]
    return snapshot,events

class IdentityGateTests(unittest.TestCase):
    def test_valid(self):
        s,e=fixture(); self.assertEqual(reconcile(s,e),{"501":"101"})
    def test_duplicate_replay(self):
        s,e=fixture(); e.append(dict(e[0])); self.assertRaisesRegex(ValueError,"sequence",reconcile,s,e)
    def test_gap(self):
        s,e=fixture(); e.append(dict(e[0],seq=3)); self.assertRaisesRegex(ValueError,"sequence",reconcile,s,e)
    def test_mixed_session(self):
        s,e=fixture(); e.append(dict(e[0],seq=2,session_id="X")); self.assertRaisesRegex(ValueError,"mixed",reconcile,s,e)
    def test_remap_callback(self):
        s,e=fixture(); e.append(dict(e[0],seq=2,actor_data_id="102")); self.assertRaisesRegex(ValueError,"remapped",reconcile,s,e)
    def test_remap_native(self):
        s,e=fixture(); e.append(dict(e[0],seq=2,actor_id=502)); self.assertRaisesRegex(ValueError,"remapped",reconcile,s,e)
    def test_missing_data_id(self):
        s,e=fixture(); e[0]["actor_data_id"]=""; self.assertRaisesRegex(ValueError,"unresolved",reconcile,s,e)
    def test_partial_snapshot(self):
        s,e=fixture(); s["has_more"]=True; self.assertRaisesRegex(ValueError,"incomplete",reconcile,s,e)
    def test_duplicate_snapshot(self):
        s,e=fixture(); s["items"][1]["native_actor_id"]="101"; self.assertRaisesRegex(ValueError,"duplicate",reconcile,s,e)
    def test_loss(self):
        s,e=fixture(); e.append(dict(e[0],seq=2,kind="bridge_loss")); self.assertRaisesRegex(ValueError,"lost",reconcile,s,e)
    def test_failed_callback_ignored(self):
        s,e=fixture(); e[0]["native_success"]=False; self.assertEqual(reconcile(s,e),{})
    def test_other_event_ignored(self):
        s,e=fixture(); e[0]["kind"]="birth_callback"; self.assertEqual(reconcile(s,e),{})
    def test_unbound_world(self):
        s,e=fixture(); e[0]["world_key"]="UNBOUND"; self.assertRaisesRegex(ValueError,"unbound",reconcile,s,e)
    def test_legacy_fields_rejected(self):
        s,e=fixture(); e[0]["sequence"]=e[0].pop("seq"); self.assertRaisesRegex(ValueError,"sequence",reconcile,s,e)
if __name__ == "__main__": unittest.main()
