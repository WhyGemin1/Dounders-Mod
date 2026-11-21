import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'experiments'))
from cycle024_daily_eligibility import snapshot
class TestCensus(unittest.TestCase):
 def test_read_only_and_shared_book(self):
  from unified_02123 import Unified223
  s=Unified223(seed=9711,digestion=True,mate_search=True)
  before=s.bridge.book.audit().copy();r=snapshot(s)
  self.assertEqual(before,s.bridge.book.audit())
  self.assertIs(s.host.book,s.bridge.book)
  self.assertEqual(r['day'],0)
 def test_no_premature_breeding_season(self):
  from unified_02123 import Unified223
  s=Unified223(seed=9711,digestion=True,mate_search=True)
  r=snapshot(s)
  self.assertEqual(r['condition_eligible_male'],0)
  self.assertEqual(r['maternal_funded_female'],0)
