import unittest
from experiments.cycle028_bottleneck import classify
from experiments.cycle026_continuity import signature
class Recovery(unittest.TestCase):
 def test_reject_duplicate_days(self):
  with self.assertRaises(ValueError):classify([{'day':40},{'day':40}])
 def test_signature_determinism(self):
  self.assertEqual(signature({'x':1}),signature({'x':1}))
 def test_preseason(self):
  self.assertEqual(classify([{'day':39,'male':1}])['breeding_observed_days'],0)
