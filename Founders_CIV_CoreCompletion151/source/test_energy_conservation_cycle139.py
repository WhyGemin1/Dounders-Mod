import unittest
from experiment_cycle136 import make_sim
from energy_conservation_cycle139 import enable_conservation, ConservationBridge139
class ConservationTests(unittest.TestCase):
 def test_opt_in(self):
  s,_=make_sim(9711,False)
  self.assertNotIsInstance(s.bridge,ConservationBridge139)
  enable_conservation(s)
  self.assertIsInstance(s.bridge,ConservationBridge139)
 def test_book_and_no_free_energy(self):
  s,_=make_sim(9711,False);enable_conservation(s)
  a=next(a for a in s.bridge.actors.values() if a.alive and a.species=='forest_browser')
  account=s.bridge.physical.reserve(a)
  before=s.bridge.book.energy[account];heat=s.bridge.book.energy['environment:heat']
  s.bridge.needs_last[a.id]='rest';s.bridge._metabolize(a)
  delta=before-s.bridge.book.energy[account]
  self.assertGreater(delta,0)
  self.assertAlmostEqual(delta,s.bridge.book.energy['environment:heat']-heat,places=9)
 def test_rest_cheaper_than_search(self):
  s,_=make_sim(9711,False);enable_conservation(s)
  a=next(a for a in s.bridge.actors.values() if a.alive and a.species=='forest_browser')
  account=s.bridge.physical.reserve(a)
  s.bridge.needs_last[a.id]='rest';before=s.bridge.book.energy[account];s.bridge._metabolize(a);rest=before-s.bridge.book.energy[account]
  s.bridge.needs_last[a.id]='search';before=s.bridge.book.energy[account];s.bridge._metabolize(a);search=before-s.bridge.book.energy[account]
  self.assertGreater(search,rest)
if __name__=='__main__':unittest.main()
