"""C063: safety and restorative decisions must not trigger opportunistic care."""
import ast
import inspect
import unittest
from core_physiology_v2 import PhysiologyBridgeV2

class TestCaregivingDecisionGate(unittest.TestCase):
    def test_step_guards_secondary_care(self):
        source = inspect.getsource(PhysiologyBridgeV2.step)
        tree = ast.parse(source)
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute) and n.func.attr == '_care']
        self.assertEqual(len(calls), 2)
        self.assertIn("not danger", source)
        self.assertIn("'hide','escape','defend','rest','sleep'", source)

if __name__ == '__main__':
    unittest.main()
