import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from interworld_split_021121 import fund_split_shipment
class SplitTests(unittest.TestCase):
 def setUp(self):
  self.s=Unified260(seed=9711,counts={k:8 for k in SPECIES},capacity_scale=.5,family_benefits=True,resource_aware_family=True)
 def test_finite_split(self):
  t=self.s.bridge.tree;b=t.book;initial=b.audit();donor=b.mass['plant:Vespara:forest'];f=b.mass[t.acct('plant','floodplain')];g=b.mass[t.acct('plant','grassland')]
  fund_split_shipment(t,.5)
  self.assertAlmostEqual(b.mass['plant:Vespara:forest'],donor-2)
  self.assertAlmostEqual(b.mass[t.acct('plant','floodplain')],f+1)
  self.assertAlmostEqual(b.mass[t.acct('plant','grassland')],g+1)
  self.assertEqual(b.audit()['rejections'],initial['rejections'])
  with self.assertRaises(ValueError):fund_split_shipment(t,.5)
 def test_invalid_fails_closed(self):
  t=self.s.bridge.tree;b=t.book;initial=b.audit()['transactions']
  for fraction in (-.1,1.1,float('nan')):
   with self.assertRaises(ValueError):fund_split_shipment(t,fraction)
  self.assertEqual(b.audit()['transactions'],initial)
if __name__=='__main__':unittest.main()
