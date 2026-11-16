"""Importer tests: set CORE151_ARCHIVE to authorized Cycle152 ZIP path."""
import os
import tempfile
import unittest
from pathlib import Path
from import_core151 import install, plan, verify_checkout
from unittest.mock import patch

ARCHIVE = os.environ.get("CORE151_ARCHIVE")


class ImportTests(unittest.TestCase):
    @unittest.skipUnless(ARCHIVE and Path(ARCHIVE).is_file(), "CORE151_ARCHIVE unavailable")
    def test_verified_archive_contains_single_world(self):
        files = plan(ARCHIVE)
        self.assertIn("founders_civ/core/ledger.py", files)
        self.assertIn("founders_civ/experimental/world_integration.py", files)

    @unittest.skipUnless(ARCHIVE and Path(ARCHIVE).is_file(), "CORE151_ARCHIVE unavailable")
    def test_import_idempotent_and_rejects_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            m = install(ARCHIVE, d)
            self.assertEqual(len(m["files"]), 27)
            self.assertEqual(m, install(ARCHIVE, d))
            p = Path(d) / "founders_civ/core/ledger.py"
            p.write_text("tampered")
            with self.assertRaises(FileExistsError):
                install(ARCHIVE, d)

    def test_checkout_provenance_rejects_unreviewed_drift(self):
        entries = {"founders_civ/core/ledger.py": b"original",
                   "run_world_tree_pilot.py": b"pilot"}
        with tempfile.TemporaryDirectory() as d, patch("import_core151.plan", return_value=entries):
            for name, content in entries.items():
                path = Path(d) / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            clean = verify_checkout("synthetic.zip", d)
            self.assertEqual(len(clean["matched"]), 2)
            path = Path(d) / "founders_civ/core/ledger.py"
            path.write_bytes(b"modified")
            with self.assertRaisesRegex(ValueError, "provenance mismatch"):
                verify_checkout("synthetic.zip", d)
            approved = verify_checkout("synthetic.zip", d, ["founders_civ/core/ledger.py"])
            self.assertIn("founders_civ/core/ledger.py", approved["overlays"])
            self.assertEqual(len(approved["matched"]), 1)
            with self.assertRaisesRegex(ValueError, "overlay not present"):
                verify_checkout("synthetic.zip", d, ["unknown.py"])
            path.unlink()
            with self.assertRaisesRegex(ValueError, "provenance mismatch"):
                verify_checkout("synthetic.zip", d, ["founders_civ/core/ledger.py"])

    def test_wrong_archive_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "wrong.zip"
            p.write_bytes(b"not source")
            with self.assertRaises(ValueError):
                plan(p)


if __name__ == "__main__":
    unittest.main()
