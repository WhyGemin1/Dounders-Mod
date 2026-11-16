"""Importer tests: set CORE151_ARCHIVE to authorized Cycle152 ZIP path."""
import os
import hashlib
import io
import json
import sys
from contextlib import redirect_stdout
import tempfile
import unittest
from pathlib import Path
from import_core151 import install, plan, verify_checkout, main
from unittest.mock import patch

ARCHIVE = os.environ.get("CORE151_ARCHIVE")


class ImportTests(unittest.TestCase):
    @unittest.skipUnless(ARCHIVE and Path(ARCHIVE).is_file(), "CORE151_ARCHIVE unavailable")

    def test_current_core151_source_matches_reviewed_fingerprints(self):
        """Exact source fingerprints: 26 archive matches; ledger overlay observed, NOT approved.

        Baseline Git blob hashes were independently computed from the authorized
        Cycle152 ZIP (SHA256 29c6bc0a...); current checkout blobs were read
        from GitHub. CI checks the current checkout without distributing the ZIP.
        """
        expected = dict(line.split() for line in """founders_civ/__init__.py bd952f68ea29e9d46d4517bd7da059eab95ec3f3
founders_civ/canon.py 7151876cfc8a6c11806fb28db49a1c8c2a562679
founders_civ/core/__init__.py e69de29bb2d1d6434b8b29ae775ad8c2e48c5391
founders_civ/core/engine.py e9dd0a6820949c8d1685045e90330b3cddd851e3
founders_civ/core/ledger.py 2d4881bcef9d4bd77ab553d66080fc5d28526ae0
founders_civ/experimental/__init__.py 59a77c176de59a7d128eb42da59c71ba9097d8c3
founders_civ/experimental/constructs.py c334cb22ea7f1537819b1f39781349d109815e3c
founders_civ/experimental/evolution.py 94b9b35660699b64ba9d4c5ae08256a157bdba2a
founders_civ/experimental/founders.py 72df20511378246de639e0b2e706651ab50ecbe7
founders_civ/experimental/social_agents.py 308a724d45afa3d412d46b66c6655524a57aa862
founders_civ/experimental/soul.py cef09d29a570310de1c280f53e740f30678cc8d0
founders_civ/experimental/world024.py 4a045794d22a18f41524b3f29ddba607571d0b2b
founders_civ/experimental/world_integration.py 3a6991330b2a516ce838368790afffba87bcd88f
founders_civ/experimental/world_trees.py 54cf3b426ad52eedbdcef9873160ef6c71e50d20
founders_civ/integration/__init__.py cd5942fdc5a052c2d786acd83d510f71a69b508e
founders_civ/integration/branches.py 28fbc5549c0879ad0d864b24cf05f8934c514ae9
founders_civ/integration/compat.py ebc168b8df51f38e9e3c48aa1175496c1cf20655
founders_civ/integration/contracts.py c6db5e367a60422922081df11dfc3996f997b1bf
founders_civ/integration/drift_audit_068.py af1ab91a5123d7e3e33c8ba1ce11d39e7f34bcf6
founders_civ/integration/drift_provenance_069.py 2d735a77ab9996edaf69379fdf5a836eb4a94301
founders_civ/integration/extensions.py ceb7e4c0f6e89fc645ab5d09f5c79a9ba28e712f
founders_civ/integration/host.py 7e9327b46ac47dd84fba219088c6bbc17b452532
founders_civ/observatory.py dbbabbde5434a9e98a72827a57fcbb28af657c11
founders_civ/runner.py 50bb0bb705797d64ad714b387e4309f2a85514b0
founders_civ/server.py adff5b1764a26eefa0cf840792a8a86169d8901d
knowledge_architecture.py 2e24f81e7d873219d048e416b31a9b6ba0610504
run_world_tree_pilot.py 2866b99e7ebf5b325e17b5091eae4806de0e7b45""".splitlines())
        self.assertEqual(len(expected), 27)
        checkout = Path(__file__).resolve().parents[1] / "src"
        for name, fingerprint in expected.items():
            with self.subTest(module=name):
                data = (checkout / name).read_bytes()
                blob = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
                self.assertEqual(hashlib.sha1(blob).hexdigest(), fingerprint)
        # The sole observed divergence from authorized ZIP is ledger.py.
        # Its historical Git blob was 2899f8eba59ded15ea5e7ce64fea2e6044f98398.
        # Pinning the current blob detects drift; it does NOT approve behavior.
        self.assertNotEqual(
            expected["founders_civ/core/ledger.py"],
            "2899f8eba59ded15ea5e7ce64fea2e6044f98398")

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

    def test_checkout_rejects_symlinked_parent_directory(self):
        entries = {"founders_civ/core/ledger.py": b"original"}
        with tempfile.TemporaryDirectory() as d, patch("import_core151.plan", return_value=entries):
            root = Path(d)
            external = root / "external"
            external.mkdir()
            (external / "ledger.py").write_bytes(b"original")
            (root / "founders_civ").mkdir()
            (root / "founders_civ/core").symlink_to(external, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "provenance mismatch"):
                verify_checkout("synthetic.zip", root)

    def test_pinned_overlay_rejects_second_unreviewed_change(self):
        entries = {"founders_civ/core/ledger.py": b"original"}
        name = "founders_civ/core/ledger.py"
        with tempfile.TemporaryDirectory() as d, patch("import_core151.plan", return_value=entries):
            path = Path(d) / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"reviewed overlay")
            expected = hashlib.sha256(b"reviewed overlay").hexdigest()
            approved = verify_checkout("synthetic.zip", d, [name], {name: expected})
            self.assertEqual(approved["overlays"][name]["checkout_sha256"], expected)
            path.write_bytes(b"unreviewed overlay")
            with self.assertRaisesRegex(ValueError, "provenance mismatch"):
                verify_checkout("synthetic.zip", d, [name], {name: expected})
            with self.assertRaisesRegex(ValueError, "fingerprint without allowlist"):
                verify_checkout("synthetic.zip", d, (), {name: expected})
            with self.assertRaisesRegex(ValueError, "invalid overlay SHA-256"):
                verify_checkout("synthetic.zip", d, [name], {name: "not-a-hash"})

    def test_cli_verify_reports_actual_matches_and_rejects_unpinned_drift(self):
        entries = {"founders_civ/core/ledger.py": b"baseline"}
        with tempfile.TemporaryDirectory() as d, patch("import_core151.plan", return_value=entries):
            path = Path(d) / "founders_civ/core/ledger.py"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"baseline")
            output = io.StringIO()
            with patch.object(sys, "argv", ["import_core151.py", "synthetic.zip", d, "--verify"]), redirect_stdout(output):
                main()
            self.assertEqual(json.loads(output.getvalue())["matched"], 1)
            path.write_bytes(b"reviewed")
            with patch.object(sys, "argv", ["import_core151.py", "synthetic.zip", d, "--verify"]):
                with self.assertRaisesRegex(ValueError, "provenance mismatch"):
                    main()
            pin = hashlib.sha256(b"reviewed").hexdigest()
            output = io.StringIO()
            with patch.object(sys, "argv", ["import_core151.py", "synthetic.zip", d, "--verify",
                                           "--overlay-sha256", f"founders_civ/core/ledger.py={pin}"]), redirect_stdout(output):
                main()
            self.assertIn("founders_civ/core/ledger.py", json.loads(output.getvalue())["overlays"])

    def test_wrong_archive_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "wrong.zip"
            p.write_bytes(b"not source")
            with self.assertRaises(ValueError):
                plan(p)


if __name__ == "__main__":
    unittest.main()
