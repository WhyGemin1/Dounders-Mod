"""Synthetic offline tests of the real M01 save/reload evidence gate.

No gameplay, real save or independent identity is claimed by this test suite.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from compare_live_snapshots import load_snapshot, compare


def snapshot(n=20):
    return {
        "world_seed": 9711, "tick": 30, "paused": True,
        "world_loading": False, "matched": n, "returned": n,
        "offset": 0, "has_more": False, "missing_identity_count": 0,
        "duplicate_identity_count": 0,
        "items": [{"native_actor_id":str(10000+i), "asset_id":"rabbit",
                   "generation":0, "parent_id_1":None, "parent_id_2":None,
                   "name":f"rabbit{i}", "x":i, "y":5} for i in range(n)]
    }


class Phase4IdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.before = Path(self.tmp.name) / "before.json"
        self.after = Path(self.tmp.name) / "after.json"
        self.write()

    def write(self, before=None, after=None):
        self.before.write_text(json.dumps(before if before is not None else snapshot()))
        self.after.write_text(json.dumps(after if after is not None else snapshot()))

    def test_same_native_ids_can_move_and_rename(self):
        after = snapshot()
        for row in after["items"]:
            row["x"] += 4
            row["name"] += "_new"
        self.write(after=after)
        result = compare(self.before, self.after)
        self.assertTrue(result["identity_and_lineage_pass"])
        self.assertFalse(result["independent_save_identity_verified"])

    def test_missing_actor_fails(self):
        after = snapshot()
        after["items"][0]["native_actor_id"] = "99999"
        self.write(after=after)
        result = compare(self.before, self.after)
        self.assertFalse(result["identity_and_lineage_pass"])
        self.assertTrue(result["new_actor_ids"])
        self.assertTrue(result["missing_or_changed"])

    def test_changed_parent_fails(self):
        after = snapshot()
        after["items"][0]["parent_id_1"] = "12"
        self.write(after=after)
        self.assertEqual(compare(self.before, self.after)["missing_or_changed"][0]["fields"],
                         ["parent_id_1"])

    def test_duplicate_rejected(self):
        after = snapshot()
        after["items"][1]["native_actor_id"] = after["items"][0]["native_actor_id"]
        self.write(after=after)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            load_snapshot(self.after)

    def test_partial_or_unpaused_rejected(self):
        for field, value in [("paused",False), ("world_loading",True),
                             ("has_more",True), ("offset",1),
                             ("missing_identity_count",1), ("duplicate_identity_count",1)]:
            after=snapshot()
            after[field]=value
            self.write(after=after)
            with self.subTest(field=field), self.assertRaisesRegex(ValueError,"Unusable"):
                load_snapshot(self.after)

    def test_world_seed_switch_rejected(self):
        after=snapshot()
        after["world_seed"]=9712
        self.write(after=after)
        with self.assertRaisesRegex(ValueError,"Different WorldBox seeds"):
            compare(self.before,self.after)

    def test_small_world_rejected(self):
        self.write(before=snapshot(19))
        with self.assertRaisesRegex(ValueError,"minimum"):
            compare(self.before,self.after)

    def test_missing_schema_rejected(self):
        after=snapshot()
        del after["items"][0]["generation"]
        self.write(after=after)
        with self.assertRaisesRegex(ValueError,"required"):
            load_snapshot(self.after)

    def test_inconsistent_counts_rejected(self):
        after=snapshot()
        after["returned"]=19
        self.write(after=after)
        with self.assertRaisesRegex(ValueError,"Partial"):
            load_snapshot(self.after)


if __name__ == "__main__":
    unittest.main()
