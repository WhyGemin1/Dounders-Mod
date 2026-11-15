import unittest
from reproductive_event_audit_02127 import audit_reproduction_events
class AuditTests(unittest.TestCase):
 def test_classifies_without_mutation(self):
  events=[{"kind":"death","species":"ridge_hound","actor":"a","cause":"starvation"},{"kind":"conception","mother":"f","due":55}]
  original=[dict(x) for x in events]
  r=audit_reproduction_events(events)
  self.assertEqual(r["hound_death_causes"],{"starvation":1})
  self.assertEqual(r["conception_due_dates"],{"f":55})
  self.assertEqual(events,original)
 def test_empty(self):
  self.assertEqual(audit_reproduction_events([])["events"],{})
