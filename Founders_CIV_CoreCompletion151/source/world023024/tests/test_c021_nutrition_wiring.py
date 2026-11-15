"""U026-C021: opt-in nutrition must remain available at low work fuel.

This is a focused regression gate for the integrated C004/C015 working tree.
It is not a claim that the complete engine source is committed to GitHub.
"""
import unittest
from unittest.mock import patch
from run_world_tree_pilot import bootstrap

class NutritionWiringTests(unittest.TestCase):
    def test_control_disabled(self):
        sim, _, _ = bootstrap(seed=820)
        self.assertFalse(sim.founder_nutrition_enabled)
    def test_low_work_fuel_keeps_nutrition_eligible(self):
        sim, _, _ = bootstrap(seed=821)
        sim.founder_nutrition_enabled = True
        with patch('founders_civ.core.founder_nutrition.propose_nutrition',
                   return_value=[(4.7,'food_digest',None,('TREE','LOT'))]):
            with patch.object(sim, '_energy', return_value=0.):
                proposals=sim._proposals('F001',[])
        self.assertTrue(any(p[1]=='food_digest' for p in proposals))
    def test_unowned_lot_rejected(self):
        sim, _, _ = bootstrap(seed=822)
        sim.founder_nutrition_enabled = True
        sim._do('F001',(4.7,'food_digest',None,('TREE','LOT')),[],None,'test-parent')
        self.assertTrue(any(e['action']=='world_action_rejected' for e in sim.events))
        self.assertLess(abs(sim.book.audit()['mass_error']),1e-7)
