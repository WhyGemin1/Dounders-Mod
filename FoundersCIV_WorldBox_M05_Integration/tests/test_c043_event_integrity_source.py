"""C043 source contract tests: real M05 queue cap and fail-closed capture gates.

These complement (but cannot replace) the dynamic Windows PowerShell fixture
tests and local WorldBox/BepInEx build/run acceptance.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class M05C043SafetyContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = (ROOT / "bridge" / "FoundersCIV_M05_Observer.cs").read_text(encoding="utf-8")
        cls.validator = (ROOT / "Phase3-CheckEvents.ps1").read_text(encoding="utf-8")
        cls.fixture = (ROOT / "tests" / "Phase3-TestFixtures.ps1").read_text(encoding="utf-8")

    def test_queue_reserves_two_slots_for_loss_marker(self):
        self.assertIn("if (_pending.Count >= MaxQueue)", self.bridge)
        self.assertIn("if (_pending.Count >= MaxQueue - 1)", self.bridge)
        self.assertIn("++_nextSequence; ++_lost;", self.bridge)
        self.assertIn("EnqueueLocked(lost);", self.bridge)
        self.assertLess(
            self.bridge.index("if (_pending.Count >= MaxQueue - 1)"),
            self.bridge.index("EnqueueLocked(lost);"),
        )

    def test_shutdown_independently_attempts_unpatch_after_drain_failure(self):
        self.assertIn("try { Drain(true); }", self.bridge)
        self.assertIn("try { if(_harmony!=null) _harmony.UnpatchSelf(); }", self.bridge)
        self.assertIn("try { if(_writer!=null) {_writer.Dispose();_writer=null;} }", self.bridge)

    def test_phase3_rejects_loss_gap_partial_session_and_unverified_hooks(self):
        for token in (
            "StreamReader(", "reader.Dispose()", "Sequence gap or duplicate", "'bridge_loss'",
            "Missing final session_close", "WorldBox assembly SHA mismatch",
            "'observer_heartbeat'", "No animal-behavior callbacks",
            "Missing or nonzero $counter", "Native hook not attached",
            "Missing/unbound session or world identity",
        ):
            self.assertIn(token, self.validator)

    def test_phase3_does_not_count_hook_probes_as_animal_behavior(self):
        self.assertIn("$behaviorKinds -contains $kind", self.validator)
        self.assertNotIn("'hook_probe', 'nutrition_call'", self.validator)

    def test_windows_fixture_suite_covers_one_pass_and_fourteen_rejections(self):
        for name in (
            "good", "seq_gap", "duplicate_seq", "missing_close",
            "bridge_loss", "missing_hook", "wrong_assembly",
            "no_behavior", "no_heartbeat", "unbound",
            "mixed_session", "callback_error", "emit_error",
            "wrong_schema", "duplicate_open",
        ):
            self.assertIn("'" + name + "'", self.fixture)
        self.assertIn("$casesRun -ne 15", self.fixture)


if __name__ == "__main__":
    unittest.main()
