import unittest,sys
sys.path.insert(0,'src')
from integrated_02196 import Unified296,ConservativeBridge296
class TestConservativeAccess(unittest.TestCase):
 def test_opt_in(self):
  s=Unified296(seed=9711,reproductive_ecology=True,capacity_scale=.5)
  self.assertIsInstance(s.bridge,ConservativeBridge296)
  self.assertFalse(s.bridge.conservative_access)
 def test_book_conservation(self):
  s=Unified296(seed=9711,reproductive_ecology=True,capacity_scale=.5,conservative_access=True)
  for _ in range(3):s.step()
  a=s.host.book.audit()
  self.assertLess(abs(a['mass_error']),1e-6)
  self.assertLess(abs(a['energy_error']),1e-5)
if __name__=='__main__':unittest.main()
