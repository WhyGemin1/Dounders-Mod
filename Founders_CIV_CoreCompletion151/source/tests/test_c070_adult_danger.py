"""Real-source isolated _choose regression; not full engine acceptance."""
import ast
import pathlib
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / 'src/core_physiology_v2.py'

class NeedsBase:
    def evaluate_needs(self, actor):
        return actor.action, .8, actor.danger

class Actor:
    stage = 'adult'
    def __init__(self, action, danger):
        self.action, self.danger = action, danger

class State:
    fatigue = .05
    readiness = .9
    sleep_pressure = .05

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse(SOURCE.read_text())
        bridge = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'PhysiologyBridgeV2')
        method = next(n for n in bridge.body if isinstance(n, ast.FunctionDef) and n.name == '_choose')
        candidate = ast.ClassDef(name='Candidate', bases=[ast.Name(id='NeedsBase', ctx=ast.Load())], keywords=[], body=[method], decorator_list=[])
        module = ast.fix_missing_locations(ast.Module(body=[candidate], type_ignores=[]))
        ns = {'NeedsBase': NeedsBase}
        exec(compile(module, str(SOURCE), 'exec'), ns)
        cls.bridge = ns['Candidate']()
        cls.bridge._state = lambda actor: State()

    def test_passive_actions_suppressed_during_danger(self):
        for action in ('feed', 'search', 'mate', 'care', 'rest', 'sleep'):
            with self.subTest(action=action):
                self.assertEqual(self.bridge._choose(Actor(action, True))[0], 'hide')

    def test_active_defense_preserved(self):
        for action in ('escape', 'defend', 'hide'):
            with self.subTest(action=action):
                self.assertEqual(self.bridge._choose(Actor(action, True))[0], action)

    def test_no_danger_normal_feeding(self):
        self.assertEqual(self.bridge._choose(Actor('feed', False))[0], 'feed')

if __name__ == '__main__':
    unittest.main()
