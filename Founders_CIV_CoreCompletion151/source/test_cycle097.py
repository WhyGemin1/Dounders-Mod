import sys,unittest
sys.path.insert(0,'src')
from integrated_02196 import Unified296
from cohort_audit_02197 import cohort_audit
class TestCohortAudit(unittest.TestCase):
 def test_nonmutating_and_deterministic(self):
  s=Unified296(seed=9711,reproductive_ecology=True,capacity_scale=.5)
  before=s.host.book.audit().copy()
  a=cohort_audit(s);b=cohort_audit(s)
  self.assertEqual(a,b)
  self.assertEqual(before,s.host.book.audit())
 def test_birth_count(self):
  s=Unified296(seed=9711,reproductive_ecology=True,capacity_scale=.5)
  for _ in range(30):s.step()
  r=cohort_audit(s)
  self.assertEqual(r['born'],len(r['cohorts']))
  self.assertEqual(r['living']+r['dead'],r['born'])
if __name__=='__main__':unittest.main()
