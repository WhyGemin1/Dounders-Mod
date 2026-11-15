import unittest, tempfile, os
from unified_02113 import Unified213
class IntegrationTests(unittest.TestCase):
    def test_shared_ledger_and_clock(self):
        s=Unified213(seed=9711);s.run(2)
        self.assertIs(s.host.book,s.bridge.book)
        self.assertEqual(s.days,2)
        self.assertEqual(len(s.host.sim.founders.people),100)
    def test_resource_debit_and_conservation(self):
        s=Unified213(seed=9712);before=s.host.book.mass[s.bridge.tree.acct('plant','grassland')]
        s.bridge.step(1)
        self.assertLess(s.host.book.mass[s.bridge.tree.acct('plant','grassland')],before)
        s.host.book.audit()
    def test_checkpoint_resume(self):
        s=Unified213(seed=9713);s.run(2)
        with tempfile.TemporaryDirectory() as d:
            path=os.path.join(d,'checkpoint.pkl');s.save(path)
            restored=Unified213.load(path)
            self.assertEqual(restored.run(2),s.run(2))
    def test_forced_collapse(self):
        s=Unified213(seed=9714);s.bridge.tree.state='archived'
        s.bridge.step(1)
        self.assertEqual(sum(s.bridge.report().values()),0)
        s.host.book.audit()
if __name__=='__main__':unittest.main()
