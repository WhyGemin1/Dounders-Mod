import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'world023024'))
from founders_civ.core.ledger import Book
from tissue_energy_02120 import fund_tissue,digest,move_carcass,decay
class TissueEnergyTests(unittest.TestCase):
 def test_funded_digest_and_carrion(self):
  b=Book();b.seed_energy('chem',10);b.freeze()
  initial=sum(b.energy.values())
  fund_tissue(b,'chem','plant_tissue',2)
  d=digest(b,'plant_tissue','grazer',1,.65)
  self.assertAlmostEqual(d.assimilated,.65)
  move_carcass(b,'plant_tissue','carrion',1)
  d2=digest(b,'carrion','hound',.5,.4)
  decay(b,'carrion',.5)
  self.assertAlmostEqual(b.energy['hound'],.2)
  self.assertAlmostEqual(sum(b.energy.values()),initial)
  self.assertAlmostEqual(b.energy['environment:heat'],1.15)
 def test_insufficient_source_fails_closed(self):
  b=Book();b.seed_energy('chem',.1);b.freeze()
  with self.assertRaises(Exception):fund_tissue(b,'chem','plant_tissue',1)
 def test_invalid_efficiency(self):
  b=Book()
  with self.assertRaises(ValueError):digest(b,'t','a',1,1.01)
 def test_zero_transfer(self):
  b=Book();digest(b,'t','a',0,.5)
  self.assertEqual(b.rejected,0)
