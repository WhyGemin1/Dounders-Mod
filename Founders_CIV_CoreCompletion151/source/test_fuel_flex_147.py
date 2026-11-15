"""Cycle147 acceptance: power != reserves, conservation, rest/food, safe fallback."""
import pickle
import unittest
from fuel_flex_147 import UnifiedFuelFlex147
from core_completion_146 import UnifiedCoreCompletion146

class FuelFlex147Tests(unittest.TestCase):
    def setUp(self):
        self.sim=UnifiedFuelFlex147(seed=100001)
        self.b=self.sim.bridge;self.book=self.b.book

    def animal(self,species='ridge_hound'):
        return next(a for a in self.b.actors.values() if a.species==species and a.alive)

    def test_01_unchanged_book_and_founders(self):
        self.assertIs(self.book,self.sim.host.book)
        self.assertIs(self.book,self.b.tree.book)
        self.assertEqual(len(self.sim.host.sim.founders.people),100)
        self.assertEqual(len({a.species for a in self.b.actors.values()}),13)
        self.assertEqual(self.book.audit()['rejections'],0)

    def test_02_stored_fuel_powers_activity_without_recent_meal(self):
        h=self.animal();ge=self.b._gut_energy(h); gut=self.b.physical.gut(h)
        initial=self.book.audit()['energy_total']
        before=self.book.energy[self.b.physical.reserve(h)]
        # Exercise uses existing body reserves; no feeding or sleep is required.
        solved=sum(self.b._work(h,'cell_movement',effort=.42) for _ in range(12))
        self.assertEqual(solved,12)
        self.assertLess(self.book.energy[self.b.physical.reserve(h)]+self.book.energy[self.b._short(h)],before+.004)
        self.assertEqual(self.book.mass[gut],0.)
        self.assertAlmostEqual(self.book.energy[ge],0.)
        self.assertAlmostEqual(self.book.audit()['energy_total'],initial,places=5)

    def test_03_stored_fuel_is_not_an_action_wallet(self):
        h=self.animal()
        # Reading a decision should never spend energy or add an action credit.
        before=dict(self.book.energy)
        self.b._choose(h)
        now=dict(self.book.energy)
        for account in set(before)|set(now):
            self.assertAlmostEqual(now.get(account,0.),before.get(account,0.),places=12)

    def test_04_mobilization_is_transfer_without_mint(self):
        h=self.animal();rapid=self.b._short(h);long=self.b.physical.reserve(h)
        short0=self.book.energy[rapid]; long0=self.book.energy[long]
        moved=self.b._mobilize(h,.0012)
        self.assertGreater(moved,0)
        self.assertAlmostEqual(self.book.energy[rapid],short0+moved,places=9)
        self.assertAlmostEqual(self.book.energy[long],long0-moved,places=9)
        self.assertEqual(self.book.audit()['rejections'],0)

    def test_05_higher_demand_does_not_create_energy(self):
        h=self.animal();before=self.book.audit()
        for _ in range(20):self.b._work(h,'strike',effort=1.5)
        after=self.book.audit()
        self.assertAlmostEqual(after['energy_total'],before['energy_total'],places=5)
        self.assertEqual(after['rejections'],0)

    def test_06_fasting_reduces_basal_but_never_zero(self):
        h=self.animal()
        normal=self.b._maintenance_demand(h)
        self.b._state(h).starvation_debt=.9
        q=self.book.energy[self.b._short(h)]
        if q:self.book.move(energy=[(self.b._short(h),'environment:heat',q)])
        r=self.book.energy[self.b.physical.reserve(h)]
        if r:self.book.move(energy=[(self.b.physical.reserve(h),'environment:heat',r)])
        fasting=self.b._maintenance_demand(h)
        self.assertGreater(fasting,normal*.80)
        self.assertLess(fasting,normal)

    def test_07_low_intensity_work_has_bounded_tissue_fallback(self):
        h=self.animal();ph=self.b.physical
        for acc in (self.b._short(h),ph.reserve(h)):
            q=self.book.energy[acc]
            if q:self.book.move(energy=[(acc,'environment:heat',q)])
        before_mass=self.book.mass[ph.live(h)]
        before_energy=self.book.audit()['energy_total']
        paid=self.b._work(h,'cell_movement',effort=.42)
        self.assertTrue(paid)
        self.assertLess(self.book.mass[ph.live(h)],before_mass)
        self.assertAlmostEqual(self.book.audit()['energy_total'],before_energy,places=5)
        self.assertEqual(self.book.audit()['rejections'],0)

    def test_08_no_tissue_funded_strikes(self):
        h=self.animal();ph=self.b.physical
        for acc in (self.b._short(h),ph.reserve(h)):
            q=self.book.energy[acc]
            if q:self.book.move(energy=[(acc,'environment:heat',q)])
        before=self.book.mass[ph.live(h)];total=self.book.audit()['energy_total']
        self.assertFalse(self.b._work(h,'strike',effort=1.8))
        self.assertEqual(self.book.mass[ph.live(h)],before)
        self.assertAlmostEqual(self.book.audit()['energy_total'],total,places=5)

    def test_09_feature_off_same_dynamics_as_core146(self):
        old=UnifiedCoreCompletion146(seed=100002)
        off=UnifiedFuelFlex147(seed=100002,fuel_flex=False)
        for _ in range(4):old.step();off.step()
        self.assertEqual(dict(old.host.book.mass),dict(off.host.book.mass))
        self.assertEqual(dict(old.host.book.energy),dict(off.host.book.energy))
        self.assertEqual([(a.id,a.alive,a.age) for a in old.bridge.actors.values()],
                         [(a.id,a.alive,a.age) for a in off.bridge.actors.values()])

    def test_10_checkpoint_exact_replay(self):
        self.sim.run(5)
        copy=pickle.loads(pickle.dumps(self.sim))
        self.sim.run(5);copy.run(5)
        self.assertEqual(dict(self.sim.host.book.energy),dict(copy.host.book.energy))
        self.assertEqual(dict(self.sim.host.book.mass),dict(copy.host.book.mass))
        self.assertEqual(dict(self.sim.bridge.fuel_flex_metrics),dict(copy.bridge.fuel_flex_metrics))
        self.assertEqual(self.book.audit()['rejections'],0)

if __name__=='__main__':unittest.main()
