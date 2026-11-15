import tempfile,unittest
from experiment_cycle135 import config,scale,start,sources,summarize,run_arm,replay30_150
class Cycle135Tests(unittest.TestCase):
 def test_config(self):
  with self.assertRaises(ValueError):config(9711,2,False,False)
  with self.assertRaises(ValueError):config(9711,4,1,False)
  with self.assertRaises(ValueError):config(1,4,True,False)
  self.assertEqual(scale(config(9711,8,True,False)),.5)
  self.assertEqual(scale(config(9711,8,True,False,'scaled_per_capita')),1.)
 def test_actual_finite_debit_and_pair_counts(self):
  c=config(9711,4,True,True);s=start(c)
  self.assertEqual(len(s.bridge.family_pairs),20)
  self.assertTrue(s.capacity_funding)
  self.assertEqual(s.capacity_funding['scale'],.5)
  self.assertEqual(s.host.book.audit()['rejections'],0)
  self.assertGreater(s.capacity_funding['transactions'],0)
  self.assertGreater(s.capacity_funding['mass'],0)
  self.assertLess(s.host.book.energy['house'],10**10)
 def test_natural_knowledge_and_replay_small(self):
  c=config(9711,4,False,True)
  with tempfile.TemporaryDirectory() as d:
   s=start(c)
   for _ in range(2):s.step()
   r=summarize(s,2,c)
   self.assertEqual(r['book_rejections'],0)
   self.assertEqual(r['living_species'].get('ridge_hound'),sum(a.alive and a.species=='ridge_hound' for a in s.bridge.actors.values()))
if __name__=='__main__':unittest.main()
