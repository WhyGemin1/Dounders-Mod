"""Self-contained tests for the U026 C051 read-only branch ancestry audit."""
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "tools/u026_c051_branch_provenance.py"
spec = importlib.util.spec_from_file_location("u026_phase1", MODULE)
phase1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(phase1)


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


class PhaseOneAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "CI Fixture")
        git(self.root, "config", "user.email", "fixture@example.invalid")
        (self.root / "seed.txt").write_text("initial\n")
        git(self.root, "add", "seed.txt")
        git(self.root, "commit", "-qm", "baseline")
        self.initial = git(self.root, "rev-parse", "HEAD")
        for branch in phase1.BRANCHES:
            git(self.root, "update-ref", f"refs/remotes/origin/{branch}", self.initial)
        for path in phase1.SOURCE_PATHS:
            dest = self.root / path
            if path.endswith("/"):
                dest = dest / "founders_civ" / "core" / "ledger.py"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text("# test fixture\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "Development implementation")
        self.dev = git(self.root, "rev-parse", "HEAD")
        git(self.root, "update-ref", "refs/remotes/origin/Development", self.dev)

    def test_origin_ancestry_and_source_presence(self):
        snapshot = phase1.audit(self.root)
        self.assertTrue(snapshot["phase_1_pass"])
        self.assertTrue(snapshot["development_checkout_matches_origin"])
        self.assertTrue(snapshot["role_branches_share_head"])
        self.assertEqual(snapshot["comparisons_to_development"]["Core"]["relation"],
                         "development_ahead")
        self.assertEqual(snapshot["comparisons_to_development"]["Core"]["development_only_commits"], 1)
        self.assertEqual(snapshot["promotion"], "NOT_ATTESTED")

    def test_divergence_does_not_claim_merge(self):
        git(self.root, "checkout", "-q", "-b", "main-fork", self.initial)
        (self.root / "unrelated.txt").write_text("release")
        git(self.root, "add", "unrelated.txt")
        git(self.root, "commit", "-qm", "main release change")
        main_sha = git(self.root, "rev-parse", "HEAD")
        git(self.root, "update-ref", "refs/remotes/origin/main", main_sha)
        result = phase1.audit(self.root)
        self.assertEqual(result["comparisons_to_development"]["main"]["relation"], "diverged")
        self.assertEqual(result["comparisons_to_development"]["main"]["base_only_commits"], 1)
        self.assertEqual(result["promotion"], "NOT_ATTESTED")

    def test_missing_origin_ref_fails_closed(self):
        git(self.root, "update-ref", "-d", "refs/remotes/origin/Integration")
        with self.assertRaises(phase1.AuditError):
            phase1.audit(self.root)

    def test_missing_engine_source_fails(self):
        (self.root / "Founders_CIV_CoreCompletion151/source/src/core_physiology_v2.py").unlink()
        git(self.root, "add", "-u")
        git(self.root, "commit", "-qm", "remove tracked physiology")
        git(self.root, "update-ref", "refs/remotes/origin/Development",
            git(self.root, "rev-parse", "HEAD"))
        result = phase1.audit(self.root)
        self.assertFalse(result["phase_1_pass"])
        self.assertIn("Founders_CIV_CoreCompletion151/source/src/core_physiology_v2.py",
                      result["missing_required_source"])


class RelationTests(unittest.TestCase):
    def test_categories(self):
        self.assertEqual(phase1.relation(0, 0), "identical")
        self.assertEqual(phase1.relation(0, 5), "development_ahead")
        self.assertEqual(phase1.relation(2, 0), "development_behind")
        self.assertEqual(phase1.relation(1, 2), "diverged")


if __name__ == "__main__":
    unittest.main()
