"""C062: danger-hide must not become a feeding action on the G3 bridge."""
import ast
import inspect
import unittest

from core_physiology_v2 import PhysiologyBridgeV2


class DangerFeedingContract(unittest.TestCase):
    def test_hide_cannot_trigger_herbivore_feeding(self):
        source = inspect.getsource(PhysiologyBridgeV2.step)
        tree = ast.parse(inspect.cleandoc(source))
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "_feed_herbivore"]
        self.assertEqual(len(calls), 1)
        # The only herbivore feed call must be nested under an explicit
        # feed/search action condition, not a hunger-only or hide condition.
        feed_call = calls[0]
        guards = [n for n in ast.walk(tree) if isinstance(n, ast.If)
                  and any(x is feed_call for x in ast.walk(n))]
        guard_texts = [ast.unparse(n.test) for n in guards]
        self.assertTrue(any("action == 'feed'" in g and
                            "action == 'search'" in g and
                            "action == 'hide'" not in g for g in guard_texts),
                        guard_texts)

if __name__ == "__main__":
    unittest.main()
