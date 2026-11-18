"""C058: dependent juveniles must sleep when safe; danger keeps caregiver behavior.

Uses the actual Core151 V2 class with stubbed base policy, no replacement engine.
"""
import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

SOURCE = Path(__file__).resolve().parents[1] / "Founders_CIV_CoreCompletion151/source/src"
sys.path.insert(0, str(SOURCE))
from core_physiology_v2 import PhysiologyBridgeV2, FunctionalState


class DependentSleepTests(unittest.TestCase):
    def setUp(self):
        self.bridge = PhysiologyBridgeV2.__new__(PhysiologyBridgeV2)
        self.actor = SimpleNamespace(id="dependent-1", stage="dependent")
        self.bridge.functional = {self.actor.id: FunctionalState()}
        self.original_evaluate = PhysiologyBridgeV2.__mro__[1].evaluate_needs

    def tearDown(self):
        PhysiologyBridgeV2.__mro__[1].evaluate_needs = self.original_evaluate

    def policy(self, danger=False):
        PhysiologyBridgeV2.__mro__[1].evaluate_needs = (
            lambda _self, _actor: ("feed", 0.7, danger)
        )

    def test_safe_dependent_high_sleep_pressure_sleeps(self):
        self.policy()
        self.bridge.functional[self.actor.id].sleep_pressure = .83
        self.assertEqual(self.bridge._choose(self.actor)[0], "sleep")

    def test_safe_dependent_high_fatigue_sleeps(self):
        self.policy()
        self.bridge.functional[self.actor.id].fatigue = .77
        self.assertEqual(self.bridge._choose(self.actor)[0], "sleep")

    def test_low_pressure_stays_with_caregiver(self):
        self.policy()
        self.assertEqual(self.bridge._choose(self.actor)[0], "stay_with_caregiver")

    def test_danger_preserves_caregiver_attachment(self):
        self.policy(danger=True)
        self.bridge.functional[self.actor.id].sleep_pressure = 1.
        self.assertEqual(self.bridge._choose(self.actor)[0], "stay_with_caregiver")

    def test_actual_sleep_reduces_pressure_without_minting_fuel(self):
        self.policy()
        s = self.bridge.functional[self.actor.id]
        s.sleep_pressure = .95
        s.fatigue = .9
        s.readiness = .2
        self.actor.condition = 1.
        self.bridge._finish_behavior(self.actor, "sleep")
        self.assertAlmostEqual(s.sleep_pressure, .66)
        self.assertAlmostEqual(s.fatigue, .67)
        self.assertAlmostEqual(s.readiness, .42)


if __name__ == "__main__":
    unittest.main()
