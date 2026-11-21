import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from interworld_capacity_021119 import fund_interworld_floodplain
class InterworldCapacityTests(unittest.TestCase):
 def setUp(self):self.s=Unified260(seed=9711,counts={k:8 for k in SPECIES},capacity_scale=.5,family_benefits=True,resource_aware_family=True)
 def test_finite_interworld_transfer(self):
  t=self.s.bridge.tree;b=t.book;before=b.audit();a=b.mass['plant:Vespara:forest'];f=b.mass[t.acct('plant','floodplain')];h=b.energy['house'];r=b.energy['river_pool'];heat=b.energy['environment:heat']
  receipt=fund_interworld_floodplain(t,2,1,.1)
  self.assertAlmostEqual(b.mass['plant:Vespara:forest'],a-2);self.assertAlmostEqual(b.mass[t.acct('plant','floodplain')],f+2)
  self.assertAlmostEqual(b.energy['house'],h-.1);self.assertAlmostEqual(b.energy['river_pool'],r-1);self.assertAlmostEqual(b.energy['environment:heat'],heat+.1)
  self.assertEqual(b.audit()['rejections'],before['rejections']);self.assertEqual(receipt['global_biomass_created'],0)
  with self.assertRaises(ValueError):fund_interworld_floodplain(t)
 def test_fail_closed_no_donor(self):
  t=self.s.bridge.tree;b=t.book;before=b.audit()
  with self.assertRaises(ValueError):fund_interworld_floodplain(t,10,10,10) if b.energy['river_pool']<10 else fund_interworld_floodplain(t,11,1,.1)
  self.assertEqual(b.audit()['transactions'],before['transactions'])
 def test_reject_nonfinite(self):
  with self.assertRaises(ValueError):fund_interworld_floodplain(self.s.bridge.tree,float('nan'))
if __name__=='__main__':unittest.main()
