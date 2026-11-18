"""G3 physiology regression: recovered actors must leave rest voluntarily.

Extracts the actual _choose method from the committed bridge source, so no
replacement engine or external package is required for this focused test.
"""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

SOURCE = Path(__file__).resolve().parents[1] / (
    "Founders_CIV_CoreCompletion151/source/src/core_physiology_v2.py"
)


def actual_choose():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body
               if isinstance(n, ast.ClassDef) and n.name == "PhysiologyBridgeV2")
    fn = next(n for n in cls.body
              if isinstance(n, ast.FunctionDef) and n.name == "_choose")
    base = type("Base", (), {"evaluate_needs": lambda self, a: ("feed", .65, False)})
    namespace = {}
    wrapper = ast.ClassDef(name="BridgeUnderTest", bases=[ast.Name(id="Base", ctx=ast.Load())],
                           keywords=[], body=[fn], decorator_list=[])
    ast.fix_missing_locations(wrapper)
    exec(compile(ast.Module(body=[wrapper], type_ignores=[]), str(SOURCE), "exec"),
         {"Base": base}, namespace)
    return namespace["BridgeUnderTest"]


class G3RestChoiceTests(unittest.TestCase):
    def actor(self, fatigue, readiness, last_behavior="sleep"):
        bridge = actual_choose()()
        state = SimpleNamespace(fatigue=fatigue, readiness=readiness,
                                last_behavior=last_behavior)
        bridge._state = lambda a: state
        return bridge

    def test_recovered_actor_can_feed_after_sleep(self):
        bridge = self.actor(.10, .90)
        self.assertEqual(bridge._choose(SimpleNamespace(stage="adult"))[0], "feed")

    def test_high_fatigue_still_sleeps(self):
        bridge = self.actor(.80, .90)
        self.assertEqual(bridge._choose(SimpleNamespace(stage="adult"))[0], "sleep")

    def test_moderate_fatigue_still_rests(self):
        bridge = self.actor(.60, .90)
        self.assertEqual(bridge._choose(SimpleNamespace(stage="adult"))[0], "rest")

    def test_dependents_stay_with_caregiver(self):
        bridge = self.actor(.10, .90)
        self.assertEqual(bridge._choose(SimpleNamespace(stage="dependent"))[0],
                         "stay_with_caregiver")


if __name__ == "__main__":
    unittest.main()
