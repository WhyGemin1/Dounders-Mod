"""G3 C057 regression: wakeful rest must not replace sleep.

These tests exercise the real Core151 V2 candidate method without constructing
an alternative Book, scheduler, or ecology engine.
"""
import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Founders_CIV_CoreCompletion151/source/src"))
from core_physiology_v2 import FunctionalState, PhysiologyBridgeV2


class WakefulRestTests(unittest.TestCase):
    def make_bridge(self, pressure=.3):
        bridge=object.__new__(PhysiologyBridgeV2)
        state=FunctionalState(fatigue=.4, readiness=.6, sleep_pressure=pressure)
        bridge.functional={"actor":state}
        bridge._fuel=lambda actor: 0.0  # no repair or energy grant
        return bridge,state,SimpleNamespace(id="actor",condition=1.0)

    def test_rest_reduces_fatigue_but_not_sleep_debt(self):
        bridge,state,actor=self.make_bridge()
        bridge._finish_behavior(actor,"rest")
        self.assertAlmostEqual(state.fatigue,.28)
        self.assertAlmostEqual(state.sleep_pressure,.312)

    def test_caregiver_wakefulness_accumulates_sleep_pressure(self):
        bridge,state,actor=self.make_bridge()
        bridge._finish_behavior(actor,"stay_with_caregiver")
        self.assertAlmostEqual(state.sleep_pressure,.32)

    def test_sleep_reduces_pressure_without_minting_fuel(self):
        bridge,state,actor=self.make_bridge()
        bridge._finish_behavior(actor,"sleep")
        self.assertAlmostEqual(state.sleep_pressure,.01)
        self.assertAlmostEqual(state.fatigue,.17)

    def test_sleep_pressure_clamps_at_one(self):
        bridge,state,actor=self.make_bridge(.999)
        bridge._finish_behavior(actor,"rest")
        self.assertEqual(state.sleep_pressure,1.0)


if __name__=="__main__":
    unittest.main()
