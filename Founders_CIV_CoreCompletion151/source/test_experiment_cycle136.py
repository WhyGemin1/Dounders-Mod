import unittest
from experiment_cycle136 import make_sim,cohort_audit
from juvenile_support_cycle136 import JuvenileSupportBridge136,ASSIST_GUARDIAN_WORK
from species_life_02115 import PROFILES
class Cycle136Tests(unittest.TestCase):
 def test_opt_in_only_and_no_second_book(self):
  a,_=make_sim(9711,False);b,_=make_sim(9711,True)
  self.assertNotIsInstance(a.bridge,JuvenileSupportBridge136)
  self.assertIsInstance(b.bridge,JuvenileSupportBridge136)
  self.assertIs(b.bridge.book,b.host.book)
  self.assertEqual(len(a.bridge.actors),len(b.bridge.actors))
 def test_natural_assisted_meal_and_book_conservation(self):
  s,_=make_sim(9711,True)
  for _ in range(160):s.step()
  metrics=s.bridge.juvenile_support_metrics
  self.assertGreater(metrics['dependent_opportunities'],0)
  self.assertGreater(metrics['successful_meals'],0,'dead dispatch path')
  self.assertGreater(metrics['caregiver_work_energy_debited'],0)
  self.assertGreater(metrics['food_mass_debited'],0)
  self.assertEqual(s.host.book.audit()['rejections'],0)
  summary,actors=cohort_audit(s)
  self.assertEqual(summary['g1_births'],len(actors))
  self.assertTrue(any(row['assisted_meals']>0 for row in actors))
 def test_species_specific_maturity(self):
  self.assertEqual(PROFILES['field_mouse'].maturity,36)
  self.assertEqual(PROFILES['ridge_hound'].maturity,180)
  self.assertGreater(PROFILES['forest_browser'].independence,PROFILES['field_mouse'].independence)
if __name__=='__main__':unittest.main()

def test_compensated_audit_rejects_material_energy_creation():
 from experiment_cycle136 import make_sim
 s,_=make_sim(9711,False)
 assert s.host.book is s.bridge.tree.book
 s.host.book.energy['house']+=.01
 import pytest
 with pytest.raises(AssertionError):s.host.book.audit()
