import unittest
from integrated_02183 import Unified283
class NatalForagingTests(unittest.TestCase):
 def test_opt_in(self):
  a=Unified283(seed=9711,reproductive_ecology=True,juvenile_foraging=True,natal_foraging=True)
  self.assertTrue(a.bridge.natal_foraging)
 def test_no_free_energy(self):
  a=Unified283(seed=9711,reproductive_ecology=True,juvenile_foraging=True,natal_foraging=True)
  before=a.host.book.audit()
  for _ in range(5):a.step()
  after=a.host.book.audit()
  self.assertLess(abs(after['mass_error']),1e-5)
  self.assertLess(abs(after['energy_error']),1e-5)
