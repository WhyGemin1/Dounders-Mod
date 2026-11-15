"""Importer tests: set CORE151_ARCHIVE to authorized Cycle152 ZIP path."""
import os
import tempfile
import unittest
from pathlib import Path
from import_core151 import install, plan

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

    def test_wrong_archive_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "wrong.zip"
            p.write_bytes(b"not source")
            with self.assertRaises(ValueError):
                plan(p)


if __name__ == "__main__":
    unittest.main()
