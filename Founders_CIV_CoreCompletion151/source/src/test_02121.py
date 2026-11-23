"""Rapid conservation and behavioral tests for the Cycle008 opt-in policy."""
import copy
import unittest
from unified_02120 import Unified220
from unified_02121 import Unified221

class TestHoundScavenging(unittest.TestCase):
    def setUp(self):
        self.s=Unified221(seed=9711,digestion=True,predator_scavenging=True)

    def _hound_carcass(self):
        hounds=[a for a in self.s.bridge.actors.values() if a.species=='ridge_hound']
        hunter,dead=hounds[:2]
        self.assertEqual(hunter.habitat,dead.habitat)
        self.s.bridge._death(dead,'controlled_carcass')
        return hunter

    def test_funded_scavenge_moves_existing_energy(self):
        hound=self._hound_carcass();b=self.s.host.book;ph=self.s.bridge.physical
        before_total=sum(b.energy.values())
        before=b.energy[ph.reserve(hound)]
        source=ph.carrion_energy(hound.habitat)
        remaining=b.energy[source]
        self.assertGreater(remaining,0)
        self.assertTrue(self.s.bridge._hunt(hound))
        self.assertGreater(b.energy[ph.reserve(hound)],before)
        self.assertLess(b.energy[source],remaining)
        self.assertAlmostEqual(sum(b.energy.values()),before_total,places=8)
        self.assertEqual(b.audit()['rejections'],0)
        self.assertEqual(self.s.bridge.stats['predator_scavenge'],1)

    def test_zero_carcass_energy_means_no_scavenge(self):
        h=self._hound_carcass();b=self.s.host.book;ph=self.s.bridge.physical
        source=ph.carrion_energy(h.habitat);q=b.energy[source]
        b.move(energy=[(source,'environment:heat',q)])
        before=b.energy[ph.reserve(h)]
        self.assertFalse(self.s.bridge._hunt(h))
        self.assertEqual(before,b.energy[ph.reserve(h)])
        self.assertEqual(self.s.bridge.stats['predator_scavenge'],0)
        self.assertEqual(b.audit()['rejections'],0)

    def test_control_mode_does_not_scavenge(self):
        control=Unified221(seed=9711,digestion=True,predator_scavenging=False)
        hounds=[a for a in control.bridge.actors.values() if a.species=='ridge_hound']
        control.bridge._death(hounds[1],'controlled_carcass')
        reserve=control.host.book.energy[control.bridge.physical.reserve(hounds[0])]
        self.assertFalse(control.bridge._hunt(hounds[0]))
        self.assertEqual(reserve,control.host.book.energy[control.bridge.physical.reserve(hounds[0])])
        self.assertEqual(control.host.book.audit()['rejections'],0)

    def test_default_preserves_v02120_control(self):
        control=Unified220(seed=9711,digestion=True)
        candidate=Unified221(seed=9711,digestion=True,predator_scavenging=False)
        a=control.run(3);b=candidate.run(3)
        for key in ('species','bridge_events','tree_state','tree_population','ledger'):
            self.assertEqual(a[key],b[key],key)
        self.assertIs(candidate.host.book,candidate.bridge.book)

    def test_restore_preserves_choice_and_ledger(self):
        self.s.run(4)
        clone=copy.deepcopy(self.s)
        self.assertEqual(self.s.run(5),clone.run(5))
        self.assertTrue(self.s.predator_scavenging)
        self.assertEqual(self.s.host.book.audit()['rejections'],0)

    def test_no_unfunded_scavenging_without_digestion(self):
        with self.assertRaises(ValueError):
            Unified221(digestion=False,predator_scavenging=True)

    def test_tree_collapse_still_kills_bridge_animals(self):
        self.s.bridge.tree.state='archived'
        self.s.bridge.step(1)
        self.assertEqual(self.s.bridge.report()['ridge_hound'],0)
        self.assertEqual(self.s.host.book.audit()['rejections'],0)

if __name__=='__main__':unittest.main()
