import unittest,sys
sys.path.insert(0,'src')
from integrated_02198 import Unified298
class TestRefuge(unittest.TestCase):
 def test_opt_in_disabled(self):
  s=Unified298(seed=9711,reproductive_ecology=True,capacity_scale=.5)
  self.assertFalse(s.bridge.juvenile_refuge)
  self.assertLess(abs(s.host.book.audit()['mass_error']),1e-7)
 def test_finite_escape(self):
  s=Unified298(seed=9711,reproductive_ecology=True,capacity_scale=.5,juvenile_refuge=True)
  b=s.bridge
  juvenile=next((a for a in b.actors.values() if a.alive and a.species in ('field_mouse','meadow_grazer','forest_browser') and a.stage=='juvenile'),None)
  if juvenile is None:
   juvenile=next(a for a in b.actors.values() if a.alive and a.species in ('field_mouse','meadow_grazer','forest_browser'))
   from species_life_02115 import PROFILES
   juvenile.age=PROFILES[juvenile.species].independence
  start=juvenile.habitat
  # Force local threat by moving an existing predator in this isolated test only.
  predator=next(a for a in b.actors.values() if a.species=='ridge_hound' and a.alive)
  predator.habitat=start
  for a in b.actors.values():
   if a.species=='ridge_hound' and a is not predator:a.habitat=start
  safe=[h for h in b.tree.habitats[start].neighbors if h!=start]
  self.assertTrue(safe)
  reserve=b.physical.reserve(juvenile)
  before=b.book.energy[reserve]
  if before < b.TRAVEL_COST+.004:
   b.book.move(energy=[('environment:sunlight',reserve,b.TRAVEL_COST+.004-before)])
   before=b.book.energy[reserve]
  self.assertTrue(b._migrate(juvenile))
  self.assertNotEqual(juvenile.habitat,start)
  self.assertAlmostEqual(b.book.energy[reserve],before-b.TRAVEL_COST)
  self.assertLess(s.host.book.audit()['mass_error'],1e-7)
if __name__=='__main__':unittest.main()
