"""Cycle005 tests: native movement friction, survival risk, accounting and replay."""
import os
import tempfile
import unittest
from unified_02115 import Unified215

EMPTY={n:0 for n in ('field_mouse','meadow_grazer','forest_browser','ridge_hound','carrion_bird')}

class ResidentMovementFrictionTests(unittest.TestCase):
    def make(self):
        s=Unified215(seed=9711,counts=EMPTY)
        s.bridge.tree.migration_cooldown_days=6  # explicit experimental opt-in
        return s

    def test_funded_move_records_history_and_cost(self):
        s=self.make();t=s.bridge.tree;b=s.host.book
        r=next(x for x in t.residents.values() if x.habitat=='forest' and x.alive)
        chem=t.acct('chem','forest')
        b.move(energy=[(chem,t.acct('heat','forest'),b.energy[chem])])
        start=b.energy[f'metabolic:{r.id}']
        self.assertTrue(t._migrate(r))
        self.assertEqual(r.last_migration_age,t.age)
        self.assertEqual(r.last_migration_origin,'forest')
        self.assertAlmostEqual(start-b.energy[f'metabolic:{r.id}'],.008)
        self.assertEqual(b.audit()['rejections'],0)

    def test_recent_move_is_deferred_without_debit(self):
        s=self.make();t=s.bridge.tree;b=s.host.book
        r=next(x for x in t.residents.values() if x.habitat=='forest' and x.alive)
        chem=t.acct('chem','forest')
        b.move(energy=[(chem,t.acct('heat','forest'),b.energy[chem])])
        self.assertTrue(t._migrate(r))
        previous=b.energy[f'metabolic:{r.id}']
        self.assertFalse(t._migrate(r))
        self.assertEqual(previous,b.energy[f'metabolic:{r.id}'])
        self.assertGreater(t.counters['tree_migration_deferred'],0)
        self.assertEqual(b.audit()['rejections'],0)

    def test_emergency_can_bypass_cooldown_without_guaranteed_success(self):
        s=self.make();t=s.bridge.tree;b=s.host.book
        r=next(x for x in t.residents.values() if x.habitat=='forest' and x.alive)
        chem=t.acct('chem','forest')
        b.move(energy=[(chem,t.acct('heat','forest'),b.energy[chem])])
        self.assertTrue(t._migrate(r))
        old=r.habitat
        target_chem=t.acct('chem',old)
        b.move(energy=[(target_chem,t.acct('heat',old),b.energy[target_chem])])
        r.health=.39
        # A second movement requires accessible energy at a neighboring site
        # and sufficient resident energy. Emergency is not a free teleport.
        self.assertTrue(t._migrate(r))
        self.assertNotEqual(r.habitat,old)
        self.assertEqual(b.audit()['rejections'],0)

    def test_control_zero_replays_old_policy_without_deferral(self):
        s=self.make();t=s.bridge.tree;b=s.host.book
        t.migration_cooldown_days=0
        r=next(x for x in t.residents.values() if x.habitat=='forest' and x.alive)
        chem=t.acct('chem','forest')
        b.move(energy=[(chem,t.acct('heat','forest'),b.energy[chem])])
        self.assertTrue(t._migrate(r))
        old=r.habitat
        chem=t.acct('chem',old)
        b.move(energy=[(chem,t.acct('heat',old),b.energy[chem])])
        before=t.counters['tree_migration_deferred']
        self.assertTrue(t._migrate(r))
        self.assertEqual(t.counters['tree_migration_deferred'],before)

    def test_checkpoint_equal_full_replay(self):
        s=self.make();s.run(15)
        with tempfile.TemporaryDirectory() as d:
            file=os.path.join(d,'save.pkl');s.save(file)
            restored=Unified215.load(file)
            self.assertEqual(s.run(15),restored.run(15))
            self.assertEqual(s.bridge.tree.counters,restored.bridge.tree.counters)
            self.assertEqual(s.host.book.audit()['rejections'],0)

if __name__=='__main__':unittest.main()
