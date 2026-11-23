"""Cycle006 tests: A-018 causal-branch guardrails, not calibration tests."""
import copy
import json
import unittest
from unified_02115 import Unified215
from experiments.realm_counterfactual_02119 import clone, digest
from founders_civ.experimental.social_agents import stable_seed

COUNTS=dict(field_mouse=8,meadow_grazer=6,forest_browser=6,ridge_hound=4,carrion_bird=4)

class TestMaintenanceCausalFork(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=Unified215(seed=9712, counts=COUNTS)
        cls.base.bridge.tree.migration_cooldown_days=6
        for _ in range(5): cls.base.step()

    def test_clones_have_same_ledger_signature(self):
        a,b=clone(self.base),clone(self.base)
        self.assertEqual(digest(a),digest(b))
        self.assertIsNot(a.host.book,b.host.book)

    def test_switch_policy_cannot_change_ledger_immediately(self):
        a,b=clone(self.base),clone(self.base)
        old=digest(a); old_seq=a.host.book.seq
        b.bridge.tree.migration_cooldown_days=0
        self.assertEqual(digest(b),old)
        self.assertEqual(b.host.book.seq,old_seq)
        self.assertEqual(b.host.book.audit()['rejections'],0)

    def test_unmodified_clones_replay_exactly(self):
        a,b=clone(self.base),clone(self.base)
        for _ in range(3): a.step();b.step()
        self.assertEqual(digest(a),digest(b))
        self.assertEqual(a.run(0) if False else a.days,b.days)

    def test_independent_founder_decision_seed(self):
        self.assertEqual(stable_seed(9712,88,'F053','decision'),stable_seed(9712,88,'F053','decision'))
        self.assertNotEqual(stable_seed(9712,88,'F053','decision'),stable_seed(9712,88,'F080','decision'))

    def test_cooldown_remains_opt_in(self):
        from founders_civ.experimental.world_trees import WorldTree
        # Initialized via canonical host, not hardwired into resident policy.
        a=clone(self.base)
        a.bridge.tree.migration_cooldown_days=0
        self.assertEqual(a.bridge.tree.migration_cooldown_days,0)
        self.assertEqual(self.base.bridge.tree.migration_cooldown_days,6)

if __name__=='__main__':unittest.main()
