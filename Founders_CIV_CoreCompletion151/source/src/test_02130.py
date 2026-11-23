import unittest
from reproductive_cohort_outcomes_02129 import cohort_outcomes
class TimeSpeciesTests(unittest.TestCase):
 def test_future_birth_cannot_close_current_pregnancy(self):
  e=[{"kind":"conception","mother":"f","day":40,"due":52},{"kind":"birth","mother":"f","day":53}]
  self.assertEqual(cohort_outcomes(e,45)["counts"],{"pending_or_due_unknown":1})
 def test_future_conception_excluded(self):
  self.assertEqual(cohort_outcomes([{"kind":"conception","mother":"f","day":50,"due":60}],45)["counts"],{})
 def test_species_scope(self):
  e=[{"kind":"conception","species":"ridge_hound","mother":"f","day":40,"due":60},{"kind":"birth","species":"field_mouse","mother":"f","day":41}]
  self.assertEqual(cohort_outcomes(e,45,species="ridge_hound")["counts"],{"pending_or_due_unknown":1})
 def test_legacy_events_still_supported(self):
  e=[{"kind":"conception","mother":"f","due":50},{"kind":"birth","mother":"f"}]
  self.assertEqual(cohort_outcomes(e,60)["counts"],{"recorded_birth":1})
