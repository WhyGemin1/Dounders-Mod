import unittest,sys
sys.path.insert(0,'src')
from integrated_02195 import Unified295,AccessibleBridge295
class AccessTest(unittest.TestCase):
 def test_opt_in(self):
  a=Unified295(seed=9711,reproductive_ecology=True,capacity_scale=.5)
  self.assertIsInstance(a.bridge,AccessibleBridge295)
  self.assertFalse(a.bridge.funded_access)
 def test_finite_book(self):
  a=Unified295(seed=9711,reproductive_ecology=True,capacity_scale=.5,funded_access=True)
  for _ in range(2):a.step()
  audit=a.host.book.audit()
  self.assertLess(abs(audit['mass_error']),1e-6)
  self.assertLess(abs(audit['energy_error']),1e-5)
if __name__=='__main__':unittest.main()
