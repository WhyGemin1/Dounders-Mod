import unittest
from run_continuity_loop import run
class ContinuityTests(unittest.TestCase):
    def test_reproducible(self):
        a=run(seed=112,days=8);b=run(seed=112,days=8)
        self.assertEqual(a,b)
    def test_funded_vs_unfunded(self):
        a=run(seed=112,days=8,refuel=True)
        b=run(seed=112,days=8,refuel=False)
        self.assertEqual(a['dimension_status'],'stable')
        self.assertEqual(b['dimension_status'],'collapsed')
    def test_checkpoint_state_loss(self):
        a=run(seed=112,days=8,shock=True)
        b=run(seed=112,days=8,shock=False)
        self.assertTrue(a['founder_reborn'])
        self.assertEqual(a['soul_states'],0)
        self.assertEqual(b['soul_states'],1)
    def test_conservation(self):
        a=run(seed=112,days=30)
        self.assertLess(abs(a['audit']['mass_error']),1e-7)
        self.assertLess(abs(a['audit']['energy_error']),1e-7)
if __name__=='__main__':unittest.main()
