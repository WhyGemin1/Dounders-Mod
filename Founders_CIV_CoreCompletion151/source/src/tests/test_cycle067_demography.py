import unittest
from cycle024_daily_eligibility import snapshot
from unified_02123 import Unified223
class TestRealDemography(unittest.TestCase):
 def test_live_state_and_no_mutation(self):
  s=Unified223(seed=9711,digestion=True,mate_search=True)
  before=s.bridge.book.audit().copy(); out=snapshot(s)
  self.assertEqual(before,s.bridge.book.audit())
  self.assertEqual(out['bridge_day'],s.bridge.day)
  self.assertEqual(sum(x['living'] for x in out['species'].values()),sum(a.alive for a in s.bridge.actors.values()))
 def test_maturity_and_funding_are_real(self):
  s=Unified223(seed=9711,digestion=True,mate_search=True)
  out=snapshot(s)
  for name,record in out['species'].items():
   self.assertLessEqual(record['maternal_funded_female'],record['condition_eligible_female'])
   self.assertLessEqual(record['colocated_funded_pairs'],record['maternal_funded_female'])
 def test_repeatable(self):
  s=Unified223(seed=9711,digestion=True,mate_search=True)
  self.assertEqual(snapshot(s),snapshot(s))
