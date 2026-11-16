"""Synthetic tests for M01 native species-cohort capture in populated worlds.

The real WorldBox DLL already supports asset_id. This tests only safe Python
argument plumbing and before/after evidence; no new C# hooks or gameplay.
"""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import m01
from compare_live_snapshots import compare


def sample(n=20, asset="rabbit"):
    return {
        "world_seed": 123456, "tick": 123, "paused": True,
        "world_loading": False, "offset": 0, "has_more": False,
        "missing_identity_count": 0, "duplicate_identity_count": 0,
        "matched": n, "returned": n, "total_scanned": 8000,
        "items": [
            {"native_actor_id": str(i+100), "asset_id": asset,
             "generation": 0, "parent_id_1": None, "parent_id_2": None}
            for i in range(n)
        ],
    }


class CohortSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "before.json"

    def capture(self, snap, asset="rabbit"):
        cli = ["m01.py", "live-snapshot", "--output", str(self.out)]
        if asset is not None:
            cli += ["--asset-id", asset]
        with patch.object(sys, "argv", cli), patch("m01.BridgeClient") as bridge:
            bridge.return_value.command.return_value = snap
            with contextlib.redirect_stdout(io.StringIO()):
                m01.main()
            return bridge.return_value.command.call_args

    def test_filtered_snapshot_sends_native_asset_id_without_truncation(self):
        args = self.capture(sample())
        self.assertEqual(args.args, ("query_actor_identities", {"asset_id": "rabbit"}))
        saved = json.loads(self.out.read_text())
        self.assertEqual(saved["capture_asset_id"], "rabbit")
        self.assertEqual(saved["total_scanned"], 8000)
        self.assertEqual(len(saved["items"]), 20)

    def test_unfiltered_snapshot_retains_existing_api(self):
        args = self.capture(sample(), asset=None)
        self.assertEqual(args.args, ("query_actor_identities", {}))
        self.assertNotIn("capture_asset_id", json.loads(self.out.read_text()))

    def test_filtered_wrong_species_refuses_and_does_not_save(self):
        with self.assertRaisesRegex(SystemExit, "2"):
            self.capture(sample(asset="wolf"))
        self.assertFalse(self.out.exists())

    def test_filtered_too_few_actors_refuses_and_does_not_save(self):
        with self.assertRaisesRegex(SystemExit, "2"):
            self.capture(sample(n=12))
        self.assertFalse(self.out.exists())

    def test_empty_filter_refuses_and_does_not_save(self):
        with self.assertRaisesRegex(SystemExit, "2"):
            self.capture(sample(), asset=" ")
        self.assertFalse(self.out.exists())

    def test_before_after_same_cohort_passes_provisionally(self):
        self.capture(sample())
        before = Path(self.tmp.name)/"before_copy.json"
        before.write_text(self.out.read_text())
        later = sample()
        later["tick"]=2
        self.capture(later)
        result = compare(before, self.out)
        self.assertTrue(result["identity_and_lineage_pass"])
        self.assertEqual(result["native_species_cohort"],"rabbit")
        self.assertFalse(result["independent_save_identity_verified"])

    def test_before_after_different_filters_fail_closed(self):
        self.capture(sample())
        before = Path(self.tmp.name)/"before_copy.json"
        before.write_text(self.out.read_text())
        later = sample(asset="wolf")
        self.capture(later, asset="wolf")
        with self.assertRaisesRegex(ValueError, "cohort filters"):
            compare(before, self.out)


if __name__ == "__main__":
    unittest.main()
