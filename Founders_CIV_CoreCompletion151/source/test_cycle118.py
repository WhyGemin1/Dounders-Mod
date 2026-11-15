import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from external_biomass_021118 import fund_external_floodplain

class ExternalBiomassTests(unittest.TestCase):
 def setUp(self):
  self.s=Unified260(seed=9711,counts={k:8 for k in SPECIES},capacity_scale=.5,family_benefits=True,resource_aware_family=True)
 def test_missing_donor_fails_closed(self):
  b=self.s.host.book;before=b.audit();dest=b.mass[self.s.bridge.tree.acct('plant','floodplain')]
  with self.assertRaises(ValueError):fund_external_floodplain(self.s.bridge.tree)
  self.assertEqual(dest,b.mass[self.s.bridge.tree.acct('plant','floodplain')]);self.assertEqual(before['transactions'],b.audit()['transactions'])
 def test_bad_amount_fails(self):
  with self.assertRaises(ValueError):fund_external_floodplain(self.s.bridge.tree,float('nan'))
 def test_reject_wrong_donor(self):
  with self.assertRaises(ValueError):fund_external_floodplain(self.s.bridge.tree,donor='plant:Solara:grassland')
if __name__=='__main__':unittest.main()

class FundedBookTransferTests(unittest.TestCase):
 def test_preseeded_external_stock_moves_conservatively(self):
  from founders_civ.core.ledger import Book
  class Tree:
   state='active';habitats={'floodplain':object()}
   def __init__(self,b):self.book=b
   def acct(self,kind,habitat):return f'{kind}:tree:test:{habitat}'
  b=Book();b.seed_mass('plant:external:founder_store',5);b.seed_mass('plant:tree:test:floodplain',1)
  b.seed_energy('river_pool',3);b.seed_energy('chem:tree:test:floodplain',1);b.freeze()
  t=Tree(b);receipt=fund_external_floodplain(t,2,1)
  self.assertEqual(b.mass['plant:external:founder_store'],3)
  self.assertEqual(b.mass['plant:tree:test:floodplain'],3)
  self.assertEqual(b.energy['river_pool'],2)
  self.assertEqual(b.energy['chem:tree:test:floodplain'],2)
  self.assertEqual(receipt['mass_debit'],2)
  self.assertEqual(b.audit()['rejections'],0)
  with self.assertRaises(ValueError):fund_external_floodplain(t,2,1)
