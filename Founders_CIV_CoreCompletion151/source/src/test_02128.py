import unittest
from reproductive_event_audit_02127 import audit_reproduction_events
class TimelineAuditTests(unittest.TestCase):
 def test_birth_closes_pregnancy(self):
  e=[{"kind":"conception","mother":"a","due":50,"day":40},{"kind":"birth","mother":"a","day":50}]
  x=audit_reproduction_events(e);self.assertEqual(x["unresolved_conceptions"],{});self.assertEqual(x["births_by_mother"],{"a":1});self.assertEqual(len(x["timeline"]),2)
 def test_unresolved_and_unknown_sex(self):
  e=[{"kind":"conception","mother":"a","due":50},{"kind":"death","species":"ridge_hound","actor":"m","cause":"starvation"}]
  x=audit_reproduction_events(e);self.assertIn("a",x["unresolved_conceptions"]);self.assertEqual(x["hound_deaths_by_sex"],{"unknown":1})
 def test_no_mutation(self):
  e=[{"kind":"conception","mother":"a"}];before=[dict(i) for i in e];audit_reproduction_events(e);self.assertEqual(e,before)
