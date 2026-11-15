import unittest
from unified_02122 import Unified222
class MateSearchTests(unittest.TestCase):
 def test_requires_funding(self):
  with self.assertRaises(ValueError):Unified222(mate_search=True)
 def test_opt_in(self):
  u=Unified222(digestion=True,mate_search=True)
  self.assertTrue(u.bridge.mate_search_enabled)
  self.assertIs(u.bridge.book,u.host.sim.world_trees.worlds[u.host.tree_id].book)
 def test_disabled(self):
  u=Unified222(digestion=True,mate_search=False)
  self.assertFalse(hasattr(u.bridge,'mate_search_enabled'))
