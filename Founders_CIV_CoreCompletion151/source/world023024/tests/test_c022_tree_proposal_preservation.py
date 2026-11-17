"""C022: optional Tree policy cannot erase legacy proposals without a funded alternative."""
import unittest
from unittest.mock import patch
from run_world_tree_pilot import bootstrap

class C022Preservation(unittest.TestCase):
    def test_no_self_tree_does_not_remove_legacy_proposals(self):
        sim, _, _ = bootstrap(seed=820)
        sim.founder_tree_independence_enabled = True
        with patch('founders_civ.core.founder_tree_agency.propose_self_trees', return_value=[]), patch('founders_civ.core.founder_tree_agency.prioritize_propagation', side_effect=lambda sim, founder, proposals: proposals):
            enabled = sim._proposals('F001', [])
        sim.founder_tree_independence_enabled = False
        control = sim._proposals('F001', [])
        self.assertEqual(enabled, control)
