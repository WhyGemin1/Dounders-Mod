import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from interworld_placement_021120 import fund_interworld_placement
class TestPlacement(unittest.TestCase):
 def setUp(self): self.s=Unified260(seed=9711,counts={k:8 for k in SPECIES},capacity_scale=.5,family_benefits=True,resource_aware_family=True)
 def test_two_destinations(self):
  for habitat in ('floodplain','grassland'):
   s=Unified260(seed=9711,counts={k:8 for k in SPECIES},capacity_scale=.5,family_benefits=True,resource_aware_family=True)
   b=s.host.book;t=s.bridge.tree;before=b.audit();d=b.mass['plant:Vespara:forest'];r=b.mass[t.acct('plant',habitat)]
   fund_interworld_placement(t,habitat)
   self.assertAlmostEqual(b.mass['plant:Vespara:forest'],d-2)
   self.assertAlmostEqual(b.mass[t.acct('plant',habitat)],r+2)
   self.assertEqual(b.audit()['rejections'],before['rejections'])
   with self.assertRaises(ValueError):fund_interworld_placement(t,habitat)
 def test_fail_closed(self):
  b=self.s.host.book;t=self.s.bridge.tree;before=b.audit()['transactions']
  for habitat,biomass in [('invalid',2),('floodplain',float('nan')),('floodplain',11)]:
   with self.assertRaises(ValueError):fund_interworld_placement(t,habitat,biomass)
  self.assertEqual(b.audit()['transactions'],before)
if __name__=='__main__':unittest.main()
