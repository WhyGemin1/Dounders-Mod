import unittest
from unified_02123 import Unified223
from funded_cohort_02125 import prepare_hound_pair
from encounter_opportunity_02124 import encounter_opportunities
class FundedCohortTests(unittest.TestCase):
 def test_funded_pair_and_conservation(self):
  s=Unified223(seed=9711,digestion=True,mate_search=True);b=s.bridge
  m0=sum(b.book.mass.values());e0=sum(b.book.energy.values())
  r=prepare_hound_pair(b)
  self.assertGreaterEqual(encounter_opportunities(b)['physically_eligible_pairs'],1)
  self.assertAlmostEqual(sum(b.book.mass.values()),m0)
  self.assertAlmostEqual(sum(b.book.energy.values()),e0)
  self.assertEqual(b.book.audit()['rejections'],0)
 def test_reject_unfunded(self):
  s=Unified223(seed=9711,digestion=True,mate_search=True);b=s.bridge
  with self.assertRaises(ValueError):prepare_hound_pair(b,maternal_fraction=2)
  self.assertEqual(b.book.audit()['rejections'],0)
 def test_partial_maternal_stock_not_ready(self):
  s=Unified223(seed=9711,digestion=True,mate_search=True);b=s.bridge
  prepare_hound_pair(b,maternal_fraction=.25)
  self.assertEqual(encounter_opportunities(b)['physically_eligible_pairs'],0)
