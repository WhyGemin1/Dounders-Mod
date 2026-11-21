import unittest,tempfile,json
from pathlib import Path
from factorial_021126 import configuration,run_arm
class FactorialTests(unittest.TestCase):
 def test_configuration_guards(self):
  with self.assertRaises(ValueError):configuration(1,memory=True,family=False)
  with self.assertRaises(ValueError):configuration(1,density=0)
 def test_funded_arm_resume(self):
  with tempfile.TemporaryDirectory() as d:
   c=configuration(9711,density=8)
   a=run_arm(c,1,d);b=run_arm(c,2,d)
   self.assertEqual(a['day'],1);self.assertEqual(b['day'],2)
   self.assertEqual(b['book']['rejections'],0)
 def test_unfunded_arm(self):
  with tempfile.TemporaryDirectory() as d:
   r=run_arm(configuration(9711,density=8,funded=False,family=False,memory=False),1,d)
   self.assertEqual(r['book']['rejections'],0)
if __name__=='__main__':unittest.main()
