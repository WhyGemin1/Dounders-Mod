"""C060 regression: execute _choose extracted from canonical Core151 V2 source."""
import ast
from pathlib import Path
import types
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "Founders_CIV_CoreCompletion151/source/src/core_physiology_v2.py"

class Base:
    def evaluate_needs(self, actor):
        return self.policy

class Actor:
    stage = "dependent"

class State:
    sleep_pressure = .95
    fatigue = .90
    readiness = .20

def load_decider():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    bridge = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "PhysiologyBridgeV2")
    method = next(n for n in bridge.body if isinstance(n, ast.FunctionDef) and n.name == "_choose")
    cls = ast.ClassDef(name="DecisionUnderTest", bases=[ast.Name(id="Base", ctx=ast.Load())],
                       keywords=[], body=[method], decorator_list=[])
    mod = ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[]))
    ns = {"Base": Base}
    exec(compile(mod, str(SOURCE), "exec"), ns)
    return ns["DecisionUnderTest"]

class C060DependentDangerTests(unittest.TestCase):
    def setUp(self):
        self.bridge = load_decider()()
        self.bridge._state = lambda a: State()
        self.actor = Actor()

    def test_danger_preserves_escape_even_when_exhausted(self):
        self.bridge.policy = ("escape", .9, True)
        self.assertEqual(self.bridge._choose(self.actor), ("escape", .9, True))

    def test_danger_preserves_defense(self):
        self.bridge.policy = ("defend", .1, True)
        self.assertEqual(self.bridge._choose(self.actor)[0], "defend")

    def test_safe_dependent_sleeps(self):
        self.bridge.policy = ("forage", .5, False)
        self.assertEqual(self.bridge._choose(self.actor)[0], "sleep")

    def test_safe_recovered_dependent_stays(self):
        self.bridge.policy = ("forage", .5, False)
        self.bridge._state = lambda a: types.SimpleNamespace(sleep_pressure=.1, fatigue=.1, readiness=.9)
        self.assertEqual(self.bridge._choose(self.actor)[0], "stay_with_caregiver")

if __name__ == "__main__":
    unittest.main()
