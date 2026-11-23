"""Cycle004 — chemical-access-aware native migration regression tests."""
import unittest
from unified_02115 import Unified215

class NativeChemicalMigrationTest(unittest.TestCase):
    def make(self):
        # All bridge counts are zero, but the original native residents remain.
        names=('field_mouse','meadow_grazer','forest_browser','ridge_hound','carrion_bird')
        return Unified215(seed=9711,counts={n:0 for n in names})

    def test_native_resident_can_move_when_plant_abundant_but_chemical_energy_empty(self):
        s=self.make();t=s.bridge.tree;b=s.host.book
        r=next(r for r in t.residents.values() if r.habitat=='forest' and r.alive)
        forest_chem=t.acct('chem','forest')
        e=b.energy[forest_chem]
        b.move(energy=[(forest_chem,t.acct('heat','forest'),e)])
        self.assertGreater(b.mass[t.acct('plant','forest')],1.)
        before=b.energy[f'metabolic:{r.id}']
        self.assertTrue(t._migrate(r))
        self.assertIn(r.habitat,t.habitats['forest'].neighbors)
        self.assertAlmostEqual(b.energy[f'metabolic:{r.id}'],before-.008)
        self.assertGreater(t.counters['tree_migration'],0)
        self.assertEqual(b.audit()['rejections'],0)

    def test_no_viable_neighbor_means_no_free_migration_or_energy(self):
        s=self.make();t=s.bridge.tree;b=s.host.book
        r=next(r for r in t.residents.values() if r.habitat=='forest' and r.alive)
        for h in ('forest',*t.habitats['forest'].neighbors):
            chem=t.acct('chem',h)
            e=b.energy[chem]
            if e>0:b.move(energy=[(chem,t.acct('heat',h),e)])
        before=b.energy[f'metabolic:{r.id}']
        self.assertFalse(t._migrate(r))
        self.assertEqual(r.habitat,'forest')
        self.assertEqual(b.energy[f'metabolic:{r.id}'],before)
        self.assertEqual(b.audit()['rejections'],0)

    def test_native_chemical_migration_deterministic_under_checkpoint(self):
        s=self.make();s.run(20)
        import tempfile,os
        with tempfile.TemporaryDirectory() as d:
            path=os.path.join(d,'ck.pkl');s.save(path)
            clone=Unified215.load(path)
            self.assertEqual(s.run(10),clone.run(10))
        self.assertEqual(s.host.book.audit()['rejections'],0)

if __name__=='__main__':unittest.main()
