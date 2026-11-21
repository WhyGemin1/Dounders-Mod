"""Functional v2 ingestion and delayed native assimilation regression gates."""
import copy
import pickle
import unittest
from core_completion_143 import UnifiedCoreCompletion143

class CoreCompletion143Tests(unittest.TestCase):
    def setUp(self):
        self.s=UnifiedCoreCompletion143(seed=100001)
        self.br=self.s.bridge
        self.book=self.s.host.book
    def actor(self):
        return next(a for a in self.br.actors.values() if a.alive and a.species=='forest_elephant')
    def resident(self):
        return next(r for r in self.br.tree.residents.values() if r.alive and r.habitat=='forest')

    def test_bridge_meal_not_taxed_by_unrelated_sun(self):
        a=self.actor();lot=self.br.lots.plant(a.habitat)
        src=self.br.tree.acct('sun',a.habitat)
        sun=self.book.energy[src]
        if sun:self.book.move(energy=[(src,'environment:heat',sun)])
        short=self.book.energy[self.br._short(a)]
        before=self.book.mass[lot.mass_account]
        self.assertTrue(self.br._feed_stock(a,lot.mass_account,'plant',dt=.25))
        self.assertLess(self.book.mass[lot.mass_account],before)
        self.assertEqual(self.book.energy[src],0.)
        self.assertEqual(self.book.energy[self.br._short(a)],short)
        self.book.audit()

    def test_native_meal_stays_in_gut_then_absorbs(self):
        r=self.resident();t=self.br.tree
        before_fuel=self.book.mass[f'fuel:{r.id}']
        before_met=self.book.energy[f'metabolic:{r.id}']
        sun=t.acct('sun',r.habitat)
        amount=self.book.energy[sun]
        if amount:self.book.move(energy=[(sun,'environment:heat',amount)])
        self.assertTrue(t._feed(r))
        self.assertEqual(before_fuel,self.book.mass[f'fuel:{r.id}'])
        self.assertEqual(before_met,self.book.energy[f'metabolic:{r.id}'])
        gut=t._native_gut(r)
        g0=self.book.mass[gut]
        self.assertGreater(g0,0)
        t._native_absorb(r)
        self.assertGreater(self.book.mass[f'fuel:{r.id}'],before_fuel)
        self.assertLess(self.book.mass[gut],g0)
        self.assertGreater(self.book.mass[gut],0)
        self.book.audit()

    def test_native_death_returns_remaining_gut_to_physical_world(self):
        r=self.resident();t=self.br.tree
        self.assertTrue(t._feed(r))
        gm=self.book.mass[t._native_gut(r)]
        rest_mass=self.book.mass[f'fuel:{r.id}']+self.book.mass[f'body:{r.id}']
        ge=self.book.energy[t._native_gut_energy(r)]
        det=self.book.mass[t.acct('detritus',r.habitat)]
        dest=f'detritus_energy:tree:{t.id}:{r.habitat}'
        before_e=self.book.energy[dest]
        t._death(r,'fixture')
        self.assertEqual(self.book.mass[t._native_gut(r)],0)
        self.assertAlmostEqual(self.book.mass[t.acct('detritus',r.habitat)],det+gm+rest_mass)
        self.assertAlmostEqual(self.book.energy[dest],before_e+ge)
        self.book.audit()

    def test_sleep_does_not_mint_and_digestion_is_independent(self):
        a=self.actor();b=self.br
        self.assertTrue(b._feed_stock(a,b.physical.plant(a),'plant',dt=.25))
        before_short=self.book.energy[b._short(a)]
        total_before=self.book.audit()['energy_total']
        b._finish_behavior(a,'sleep',dt=.25)
        self.assertAlmostEqual(self.book.audit()['energy_total'],total_before)
        b._digest(a,.25)
        self.assertGreater(self.book.energy[b._short(a)],before_short)
        self.book.audit()

    def test_single_book_two_demographics_and_no_time_wallet(self):
        self.assertIs(self.book,self.br.tree.book)
        self.assertIs(self.book,self.br.book)
        self.assertIs(self.book,self.s.host.book)
        self.assertFalse(hasattr(self.actor(),'time_wallet'))
        self.assertFalse(hasattr(self.resident(),'time_wallet'))
        self.assertNotEqual(type(self.br).__name__,type(self.br.tree).__name__)
        self.s.step()
        self.assertEqual(self.s.days,self.br.day)
        self.assertEqual(self.book.audit()['rejections'],0)

    def test_ingestion_rejects_mismatched_energy_and_owner_atomically(self):
        a=self.actor();lot=self.br.lots.plant(a.habitat)
        before_m=self.book.mass[lot.mass_account]
        before_e=self.book.energy[lot.energy_account]
        wrong=f'gut_energy:wrong_animal'
        with self.assertRaises(ValueError):
            self.book.ingest(material=[(lot.mass_account,self.br.physical.gut(a),.001)],
                 energy=[(lot.energy_account,wrong,.0003)])
        self.assertEqual(self.book.mass[lot.mass_account],before_m)
        self.assertEqual(self.book.energy[lot.energy_account],before_e)
        self.assertEqual(self.book.energy[wrong],0)
        self.assertEqual(self.book.rejected,1)

    def test_selection_is_not_energy_payment(self):
        a=self.actor();b=self.br
        reserve_before=self.book.energy[b.physical.reserve(a)]
        short_before=self.book.energy[b._short(a)]
        seq=self.book.seq
        action,_,_=b._choose(a)
        self.assertIn(action,('feed','rest','sleep','hide'))
        self.assertEqual(self.book.seq,seq)
        self.assertEqual(self.book.energy[b.physical.reserve(a)],reserve_before)
        self.assertEqual(self.book.energy[b._short(a)],short_before)

    def test_pickle_replay(self):
        for _ in range(3):self.s.step()
        restored=pickle.loads(pickle.dumps(self.s))
        for _ in range(3):self.s.step();restored.step()
        self.assertEqual(self.s.report()['core_completion_143'],restored.report()['core_completion_143'])
        self.assertEqual(self.s.host.book.audit(),restored.host.book.audit())

if __name__=='__main__':unittest.main()
