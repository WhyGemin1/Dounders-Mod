import unittest
from types import SimpleNamespace
from clock_provenance_02133 import clock_provenance, assert_clock_provenance
class ClockProvenanceTests(unittest.TestCase):
    def fixture(self, tick=63, bootstrap=3, days=60, bridge=60):
        book=object()
        engine=SimpleNamespace(tick=tick,ecology=SimpleNamespace(day=tick),book=book)
        host=SimpleNamespace(sim=engine,bootstrap_tick=bootstrap,book=book)
        return SimpleNamespace(host=host,bridge=SimpleNamespace(day=bridge,book=book),days=days)
    def test_bootstrap_offset_is_not_drift(self):
        self.assertEqual(assert_clock_provenance(self.fixture())['bootstrap_tick'],3)
    def test_real_drift_rejected(self):
        with self.assertRaises(AssertionError):assert_clock_provenance(self.fixture(bridge=59))
    def test_nonshared_book_rejected(self):
        s=self.fixture();s.bridge.book=object()
        with self.assertRaises(AssertionError):assert_clock_provenance(s)
    def test_absolute_ecology_clock_divergence(self):
        s=self.fixture();s.host.sim.ecology.day=62
        self.assertFalse(clock_provenance(s)['clock_consistent'])
if __name__=='__main__':unittest.main()
