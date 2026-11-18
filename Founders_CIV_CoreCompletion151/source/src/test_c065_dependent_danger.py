"""C065: danger must override passive juvenile foraging decisions."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from core_physiology_v2 import PhysiologyBridgeV2, FunctionalState

class DependentDangerTests(unittest.TestCase):
    def test_passive_actions_hide_when_dangerous(self):
        actor=SimpleNamespace(id="juvenile-1",stage="dependent")
        bridge=SimpleNamespace(functional={"juvenile-1":FunctionalState()})
        for action in ("rest","sleep","stay_with_caregiver","care","feed","search","mate"):
            with self.subTest(action=action):
                with patch.object(PhysiologyBridgeV2.__bases__[0], "evaluate_needs", return_value=(action,.9,True)):
                    self.assertEqual(PhysiologyBridgeV2._choose(bridge,actor)[0],"hide")
    def test_active_defense_is_preserved(self):
        actor=SimpleNamespace(id="juvenile-1",stage="dependent")
        bridge=SimpleNamespace(functional={"juvenile-1":FunctionalState()})
        for action in ("escape","defend","hide"):
            with self.subTest(action=action):
                with patch.object(PhysiologyBridgeV2.__bases__[0], "evaluate_needs", return_value=(action,.9,True)):
                    self.assertEqual(PhysiologyBridgeV2._choose(bridge,actor)[0],action)
    def test_safe_dependent_remains_with_caregiver(self):
        actor=SimpleNamespace(id="juvenile-1",stage="dependent")
        bridge=SimpleNamespace(functional={"juvenile-1":FunctionalState()})
        with patch.object(PhysiologyBridgeV2.__bases__[0], "evaluate_needs", return_value=("feed",.8,False)):
            self.assertEqual(PhysiologyBridgeV2._choose(bridge,actor)[0],"stay_with_caregiver")

if __name__=="__main__":unittest.main()
