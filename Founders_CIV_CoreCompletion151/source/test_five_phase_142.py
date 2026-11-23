"""Five-phase tests on the real WORLD-023 Book and five-habitat bridge."""
import copy
import unittest
from collections import Counter
from five_phase_core_142 import UnifiedFivePhase142, PLANT_EDIBLE_ENERGY_DENSITY


class FivePhase142Test(unittest.TestCase):
    def setUp(self):
        self.s=UnifiedFivePhase142(seed=100001)
        self.b=self.s.bridge
        self.book=self.b.book

    def actor(self, species):
        return next(x for x in self.b.actors.values() if x.alive and x.species==species)

    def test_single_book_clock_founder_and_species(self):
        self.assertIs(self.s.host.book,self.b.book)
        self.assertIs(self.b.book,self.b.tree.book)
        self.assertEqual(len(self.s.host.sim.founders.people),100)
        self.assertEqual(len({a.species for a in self.b.actors.values()}),13)
        self.assertGreater(self.s.world_support.totals['creation_energy'],0)
        self.s.step()
        self.assertEqual(self.s.days,self.b.day)
        self.assertEqual(self.book.audit()['rejections'],0)

    def test_paired_lot_native_and_bridge(self):
        lot=self.b.lots.plant('forest')
        self.assertGreater(self.book.mass[lot.mass_account],0)
        self.assertGreater(self.book.energy[lot.energy_account],0)
        # Native residents eat using this same account, not from chem.
        original=self.book.energy[lot.energy_account]
        native=next(r for r in self.b.tree.residents.values() if r.alive and r.habitat=='forest')
        # Native resident no longer needs independent chem per-meal credits.
        chem=self.b.tree.acct('chem','forest')
        q=self.book.energy[chem]
        if q:self.book.move(energy=[(chem,'environment:heat',q)])
        did=self.b.tree._feed(native)
        self.assertTrue(did)
        self.assertLess(self.book.energy[lot.energy_account],original)
        self.assertEqual(self.book.energy[chem],0.)

    def test_bridge_mass_and_energy_debited_atomically(self):
        a=self.actor('forest_elephant')
        lot=self.b.lots.plant(a.habitat)
        before_m=self.book.mass[lot.mass_account]
        before_e=self.book.energy[lot.energy_account]
        before_g=self.book.mass[self.b.physical.gut(a)]
        success=self.b._feed_stock(a,lot.mass_account,'plant',dt=.25)
        self.assertTrue(success)
        consumed=self.book.mass[self.b.physical.gut(a)]-before_g
        self.assertGreater(consumed,0)
        self.assertAlmostEqual(before_m-self.book.mass[lot.mass_account],consumed,8)
        self.assertAlmostEqual(before_e-self.book.energy[lot.energy_account],
                               consumed*PLANT_EDIBLE_ENERGY_DENSITY,8)
        self.book.audit()

    def test_feeding_is_not_immediate_metabolism(self):
        a=self.actor('forest_elephant')
        short=self.b._short(a)
        before=self.book.energy[short]
        food=self.b.physical.plant(a)
        self.assertTrue(self.b._feed_stock(a,food,'plant',dt=.25))
        self.assertAlmostEqual(before,self.book.energy[short],9)
        self.b._digest(a,dt=.25)
        self.assertGreater(self.book.energy[short],before)

    def test_ongoing_processes_no_time_currency(self):
        a=self.actor('woolly_mammoth')
        self.assertFalse(hasattr(a,'time_budget'))
        self.assertEqual(self.b.substeps,4)
        self.assertTrue(self.b._feed_stock(a,self.b.physical.plant(a),'plant',dt=.25))
        g1=self.book.mass[self.b.physical.gut(a)]
        self.b._digest(a,dt=.25)
        self.assertLess(self.book.mass[self.b.physical.gut(a)],g1)
        self.assertTrue(self.b._feed_stock(a,self.b.physical.plant(a),'plant',dt=.25))
        # Multiple actual feeds in one simulated day, no action wallet.
        self.assertGreaterEqual(self.b.physiology_metrics['paired_lot_meals'],2)
        self.book.audit()

    def test_legacy_feed_caller_uses_physical_substep_duration(self):
        a=self.actor('forest_elephant')
        self.b._current_dt=.25
        lot=self.b.lots.plant(a.habitat)
        before=self.book.mass[lot.mass_account]
        self.assertTrue(self.b._feed_stock(a,lot.mass_account,'plant'))
        q=before-self.book.mass[lot.mass_account]
        expected_daily=self.b._bodymass(a)*.075
        self.assertLessEqual(q,expected_daily*.25+1e-9)

    def test_rest_no_minted_energy(self):
        a=self.actor('field_mouse')
        s=self.b._state(a)
        s.fatigue=.76
        before=self.book.audit()['energy_total']
        self.b._finish_behavior(a,'sleep',dt=.25)
        self.assertLess(s.fatigue,.76)
        self.assertAlmostEqual(self.book.audit()['energy_total'],before,7)

    def test_energy_matches_trophic_meat_lots(self):
        rabbit=self.actor('burrow_rabbit')
        a=self.actor('red_fox')
        tissue=self.b.physical.tissue(rabbit)
        self.assertGreater(self.book.energy[tissue],.1*self.book.mass[self.b.physical.live(rabbit)])
        # Carcass is paired with its own energy account, not plant chem.
        carcass=self.b.lots.carrion('forest')
        self.assertEqual(carcass.energy_account,self.b.physical.carrion_energy('forest'))
        self.book.audit()

    def test_response_to_gut_and_local_danger(self):
        a=self.actor('forest_elephant')
        # An elephant's perceived danger is not every distant predator in habitat.
        action,hunger,danger=self.b._choose(a)
        self.assertFalse(danger)
        self.assertIn(action,('feed','rest','sleep','hide'))

    def test_real_birth_from_maternal_mass_energy(self):
        mother=next(x for x in self.b.actors.values() if x.alive and x.sex=='F'
                    and x.species=='burrow_rabbit')
        p=__import__('species_life_02115').PROFILES[mother.species]
        # Reference cohort has purchased enough maternal tissue; no free seed.
        needed=p.newborn_mass()*2
        mater=self.b.physical.maternal(mother)
        store=self.book.mass[mater]
        if store<needed:
            shortage=needed-store
            src=self.b.physical.plant(mother)
            self.b.physical.convert([(src,mater,shortage)])
        maternal_energy=self.b.physical.maternal_energy(mother)
        gap=max(0.,needed*.45-self.book.energy[maternal_energy])
        if gap:
            donor=self.b.tree.acct('chem',mother.habitat)
            self.book.move(energy=[(donor,maternal_energy,gap)])
        mother.pregnant_until=self.b.day
        father=next(x for x in self.b.actors.values() if x.species==mother.species and x.sex=='M')
        mother.pregnancy_father=father.id
        count=self.b._birth(mother)
        self.assertGreaterEqual(count,1)
        babies=[x for x in self.b.actors.values() if x.parent==mother.id]
        self.assertEqual(len(babies),count)
        self.assertTrue(all(self.book.energy[self.b.physical.tissue(x)]>0 for x in babies))
        self.assertTrue(all(x.stage=='dependent' for x in babies))
        self.book.audit()

    def test_disturbance_can_deplete_edible_energy(self):
        a=self.actor('forest_elephant')
        lot=self.b.lots.plant(a.habitat)
        energy=self.book.energy[lot.energy_account]
        if energy:self.book.move(energy=[(lot.energy_account,'environment:heat',energy)])
        chemical=self.b.physical.chem(a)
        source=self.book.energy[chemical]
        if source:self.book.move(energy=[(chemical,'environment:heat',source)])
        self.assertFalse(self.b._feed_stock(a,lot.mass_account,'plant',dt=.25))
        self.book.audit()

    def test_unbalanced_ledger_still_rejected(self):
        # Tampering with Book state outside its transaction interface must be
        # detected even though native host now uses a scale-aware tolerance.
        self.book.energy['house']+=.01
        with self.assertRaises(AssertionError):self.book.audit()

    def test_pickle_checkpoint_exact_replay(self):
        import pickle
        for _ in range(3):self.s.step()
        saved=pickle.loads(pickle.dumps(self.s))
        for _ in range(3):self.s.step();saved.step()
        self.assertEqual(self.s.bridge.five_phase_report(),saved.bridge.five_phase_report())
        self.assertEqual(self.s.host.book.audit(),saved.host.book.audit())

    def test_checkpoint_exact_replay(self):
        for _ in range(4):self.s.step()
        saved=copy.deepcopy(self.s)
        for _ in range(5):self.s.step()
        for _ in range(5):saved.step()
        self.assertEqual(self.s.bridge.five_phase_report(),saved.bridge.five_phase_report())
        self.assertEqual(self.s.host.book.audit(),saved.host.book.audit())


if __name__=='__main__':unittest.main()
