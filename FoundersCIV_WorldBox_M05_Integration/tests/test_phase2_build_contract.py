"""Fail-closed source checks for Phase 2 M05.3 build packaging.

These tests do NOT prove a native Windows compile, plugin load, or WorldBox
gameplay session. A build on the real Windows host is separately required.
"""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = "51d275f0168be2f6ca26341ab292406714e694e0270eafcb25b999d5df6dd69f"


class Phase2BuildContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proj = ROOT / "bridge" / "FoundersCIV_M05_Observer.csproj"
        cls.source = (ROOT / "bridge" / "FoundersCIV_M05_Observer.cs").read_text(encoding="utf-8")
        cls.script = (ROOT / "build_bridge.ps1").read_text(encoding="utf-8")
        cls.xml = ET.parse(cls.proj).getroot()

    def test_compiler_references_all_six_local_dependencies(self):
        references = {e.attrib["Include"] for e in self.xml.findall(".//Reference")}
        self.assertEqual(
            references,
            {"BepInEx", "0Harmony", "UnityEngine", "UnityEngine.CoreModule",
             "UnityEngine.IMGUIModule", "UnityEngine.JSONSerializeModule"},
        )
        self.assertEqual(self.xml.findtext(".//TargetFramework"), "net462")
        self.assertNotIn("Assembly-CSharp", references)

    def test_source_has_m053_harmony_and_json_serializer_fix(self):
        self.assertIn('"0.5.3"', self.source)
        self.assertIn("new HarmonyMethod(finalizer), null);", self.source)
        self.assertNotIn("null, finalizer == null ? null : new HarmonyMethod(finalizer));",
                         self.source)
        self.assertIn("JsonUtility.ToJson", self.source)

    def test_installer_fails_closed_on_assembly_mismatch(self):
        self.assertIn(EXPECTED, self.script)
        self.assertIn("MISMATCH_FAIL_CLOSED", self.script)
        self.assertIn("Get-FileHash", self.script)
        self.assertIn("throw", self.script)
        self.assertIn("if (-not $Install)", self.script)

    def test_installer_stages_local_references_without_shipping_game_dlls(self):
        for dll in (
            "BepInEx.dll", "0Harmony.dll", "UnityEngine.dll",
            "UnityEngine.CoreModule.dll", "UnityEngine.IMGUIModule.dll",
            "UnityEngine.JSONSerializeModule.dll",
        ):
            self.assertIn(dll, self.script)
        self.assertIn("build\\refs", self.script)
        self.assertIn("dependency_manifest.json", self.script)
        self.assertIn("plugin_backups", self.script)
        self.assertIn("Installed DLL hash mismatch", self.script)

    def test_native_observer_has_seven_monitored_methods(self):
        for method in (
            "addNutritionFromEating", "consumeFoodResource",
            "newKillAction", "createBabyActorFromData", "birthEvent",
            "getNutrition", "hasDied",
        ):
            self.assertIn(method, self.source)
        self.assertIn("const int MaxQueue = 50000", self.source)


if __name__ == "__main__":
    unittest.main()
