import unittest,tempfile
from capacity_dose_021131 import dose_config,run,replay
class DoseTests(unittest.TestCase):
 def test_invalid_dose(self):
  for x in [-1,float('nan'),3]:
   with self.assertRaises(ValueError):dose_config(9711,dose=x)
 def test_conserved_replay(self):
  with tempfile.TemporaryDirectory() as d:
   c=dose_config(9711,family=False,memory=False,dose=.5)
   rows=run(c,[1,2],d)
   self.assertEqual(replay(c,d,1,2)['living'],rows[-1]['living'])
   self.assertEqual(rows[-1]['book']['rejections'],0)
if __name__=='__main__':unittest.main()
