import unittest
from unified_02123 import Unified223
from encounter_opportunity_02124 import encounter_opportunities
from species_life_02115 import PROFILES,MASS_SCALE
class OpportunityTests(unittest.TestCase):
 def test_diagnostic_read_only(self):
  s=Unified223(seed=9711,digestion=True,mate_search=True)
  before=(dict(s.host.book.energy),dict(s.host.book.mass))
  result=encounter_opportunities(s.bridge)
  self.assertEqual(before,(dict(s.host.book.energy),dict(s.host.book.mass)))
  self.assertEqual(result['population'],4)
 def test_adjacency_and_maternal_gates(self):
  s=Unified223(seed=9711,digestion=True,mate_search=True);b=s.bridge
  f=next(a for a in b.actors.values() if a.species=='ridge_hound' and a.sex=='F' and a.stage=='adult')
  m=next(a for a in b.actors.values() if a.species=='ridge_hound' and a.sex=='M' and a.stage=='adult')
  f.age=m.age=PROFILES['ridge_hound'].maturity+1;f.condition=m.condition=1
  m.habitat=tuple(b.tree.habitats[f.habitat].neighbors)[0]
  r=encounter_opportunities(b);self.assertGreaterEqual(r['adjacent_pairs'],1)
  self.assertEqual(r['physically_eligible_pairs'],0)
  cost=PROFILES['ridge_hound'].birth_cost*MASS_SCALE
  short=max(0,cost-b.book.mass[b.physical.maternal(f)])
  if short:b.physical.convert([(b.physical.plant(f),b.physical.maternal(f),short)])
  self.assertGreaterEqual(encounter_opportunities(b)['physically_eligible_pairs'],1)
  self.assertEqual(b.book.audit()['rejections'],0)
