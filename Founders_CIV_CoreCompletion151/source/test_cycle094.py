import sys,unittest
sys.path.insert(0,'src')
from integrated_02194 import Unified294
class AccessTests(unittest.TestCase):
 def test_opt_in_audit_does_not_change_book(self):
  a=Unified294(seed=9711,reproductive_ecology=True,juvenile_foraging=True,capacity_scale=.5,edible_budget=0)
  b=a.host.book.audit().copy()
  for _ in range(30):a.step()
  self.assertEqual(len(a.access_snapshots),1)
  self.assertEqual(a.access_snapshots[0]['day'],30)
  self.assertEqual(a.access_snapshots[0]['living'],sum(x.alive for x in a.bridge.actors.values()))
  self.assertAlmostEqual(a.host.book.audit()['mass_error'],b['mass_error'],places=5)
 def test_funding_events_count_is_consistent(self):
  a=Unified294(seed=9711,reproductive_ecology=True,juvenile_foraging=True,capacity_scale=.5,edible_budget=1,scheduled_funding=True)
  for _ in range(30):a.step()
  self.assertEqual(a.access_snapshots[0]['funded_events'],sum(bool(e.get('funded')) for e in a.edible_events))
if __name__=='__main__':unittest.main()
