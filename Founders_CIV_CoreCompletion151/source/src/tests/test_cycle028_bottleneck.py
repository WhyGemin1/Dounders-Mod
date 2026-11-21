import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'experiments'))
from cycle028_bottleneck import classify
class BottleneckTests(unittest.TestCase):
 def row(self,d,male=1,adult=1,funded=0,pair=0):
  return dict(day=d,bridge_day=d,male=male,adult_male=adult,condition_eligible_male=adult,condition_eligible_female=1,maternal_funded_female=funded,colocated_funded_pairs=pair,conceptions=0,births=0,ledger_rejections=0)
 def test_preseason_excluded(self):
  r=classify([self.row(39,pair=1),self.row(40,pair=0)])
  self.assertEqual(r['breeding_observed_days'],1);self.assertIsNone(r['first_day_with_funded_colocation'])
 def test_funded_opportunity(self):
  r=classify([self.row(40),self.row(41,funded=1,pair=1)])
  self.assertEqual(r['first_day_with_funded_colocation'],41)
 def test_male_extinction(self):
  r=classify([self.row(40),self.row(41,male=0,adult=0)])
  self.assertEqual(r['last_day_with_living_male'],40)
 def test_order_validation(self):
  with self.assertRaises(ValueError):classify([self.row(40),self.row(40)])
if __name__=='__main__':unittest.main()
