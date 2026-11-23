import unittest
from unified_02123 import Unified223
from funded_cohort_02125 import prepare_hound_pair
from reproduction_trace_02126 import trace_hound_gates
class TraceTests(unittest.TestCase):
 def test_trace_is_read_only(self):
  s=Unified223(seed=9711,digestion=True,mate_search=True);b=s.bridge
  before=(dict(b.book.mass),dict(b.book.energy))
  t=trace_hound_gates(b)
  self.assertEqual(t['population'],4)
  self.assertEqual(before,(dict(b.book.mass),dict(b.book.energy)))
 def test_prepared_pair_opportunity(self):
  s=Unified223(seed=9711,digestion=True,mate_search=True);b=s.bridge
  prepare_hound_pair(b)
  self.assertGreaterEqual(trace_hound_gates(b)['local_ready_females'],1)
  self.assertEqual(b.book.audit()['rejections'],0)
