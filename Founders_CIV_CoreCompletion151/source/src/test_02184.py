import unittest
from integrated_02184 import Unified284

class LactationTests(unittest.TestCase):
    def test_opt_in(self):
        x=Unified284(seed=9711,lactation_growth=True,reproductive_ecology=True,juvenile_foraging=True)
        self.assertTrue(x.bridge.lactation_growth)
        self.assertEqual(x.days,0)
    def test_opt_out(self):
        x=Unified284(seed=9711,lactation_growth=False,reproductive_ecology=True)
        self.assertFalse(x.bridge.lactation_growth)
    def test_conservation_and_step(self):
        x=Unified284(seed=9711,lactation_growth=True,reproductive_ecology=True,juvenile_foraging=True)
        before=x.host.book.audit()
        for _ in range(3):x.step()
        after=x.host.book.audit()
        self.assertAlmostEqual(before['mass_error'],after['mass_error'],places=6)
        self.assertAlmostEqual(before['energy_error'],after['energy_error'],places=6)
