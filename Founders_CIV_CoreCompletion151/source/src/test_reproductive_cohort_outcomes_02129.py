import unittest
from reproductive_cohort_outcomes_02129 import cohort_outcomes
class CohortTests(unittest.TestCase):
 def test_birth(self):
  r=cohort_outcomes([{"kind":"conception","mother":"a","due":10},{"kind":"birth","mother":"a"}],20);self.assertEqual(r["counts"],{"recorded_birth":1})
 def test_overdue_not_miscarriage(self):
  r=cohort_outcomes([{"kind":"conception","mother":"a","due":10}],20);self.assertEqual(r["counts"],{"overdue_no_recorded_birth":1})
 def test_maternal_death(self):
  r=cohort_outcomes([{"kind":"conception","mother":"a","due":10},{"kind":"death","actor":"a"}],20);self.assertEqual(r["counts"],{"maternal_death_no_recorded_birth":1})
 def test_pending(self):
  r=cohort_outcomes([{"kind":"conception","mother":"a","due":30}],20);self.assertEqual(r["counts"],{"pending_or_due_unknown":1})
 def test_reconception_not_birth(self):
  r=cohort_outcomes([{"kind":"conception","mother":"a","due":10},{"kind":"conception","mother":"a","due":20}],15);self.assertEqual(r["counts"],{"superseded_unresolved":1,"pending_or_due_unknown":1})
if __name__=="__main__":unittest.main()
