"""Synthetic archive safety tests. No real Core151 archive required."""
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from import_core151 import plan, install, digest, ROOT, REQUIRED

def make_zip(path, extras=(), duplicate=False):
    with zipfile.ZipFile(path, "w") as z:
        for name in REQUIRED:
            z.writestr(ROOT + name, b"# fixture\n")
        for name, data in extras:
            z.writestr(ROOT + name, data)
        if duplicate:
            z.writestr(ROOT + REQUIRED[0], b"# duplicate\n")

class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.archive = Path(self.temp.name) / "archive.zip"
        self.dest = Path(self.temp.name) / "dest"

    def allowed(self):
        return patch("import_core151.SOURCE_SHA256", digest(self.archive.read_bytes()))

    def test_fixture_import_and_idempotence(self):
        make_zip(self.archive)
        with self.allowed():
            self.assertEqual(install(self.archive, self.dest),
                             install(self.archive, self.dest))
            self.assertEqual(len(plan(self.archive)), 5)

    def test_duplicate_member_rejected(self):
        make_zip(self.archive, duplicate=True)
        with self.allowed(), self.assertRaisesRegex(ValueError, "duplicate"):
            plan(self.archive)

    def test_traversal_rejected(self):
        make_zip(self.archive, [("founders_civ/../../escape.py", b"bad")])
        with self.allowed(), self.assertRaisesRegex(ValueError, "unsafe"):
            plan(self.archive)

    def test_size_limit_rejected(self):
        make_zip(self.archive, [("founders_civ/large.py", b"x"*64)])
        with self.allowed(), patch("import_core151.MAX_FILE_BYTES", 32), self.assertRaisesRegex(ValueError, "limit"):
            plan(self.archive)

    def test_symlink_destination_rejected(self):
        make_zip(self.archive)
        self.dest.mkdir()
        (self.dest / "founders_civ").symlink_to(Path(self.temp.name), target_is_directory=True)
        with self.allowed(), self.assertRaisesRegex(ValueError, "symlink"):
            install(self.archive, self.dest)

    def test_modified_file_rejected(self):
        make_zip(self.archive)
        with self.allowed():
            install(self.archive, self.dest)
            (self.dest / REQUIRED[0]).write_text("tampered")
            with self.assertRaises(FileExistsError):
                install(self.archive, self.dest)

    def test_dry_run_has_no_writes(self):
        make_zip(self.archive)
        with self.allowed():
            install(self.archive, self.dest, dry_run=True)
            self.assertFalse(self.dest.exists())

    def test_wrong_hash_rejected(self):
        make_zip(self.archive)
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            plan(self.archive)

    def test_missing_dependencies_rejected(self):
        with zipfile.ZipFile(self.archive, "w") as z:
            z.writestr(ROOT + REQUIRED[0], b"x")
        with self.allowed(), self.assertRaisesRegex(ValueError, "missing"):
            plan(self.archive)

if __name__ == "__main__":
    unittest.main()
