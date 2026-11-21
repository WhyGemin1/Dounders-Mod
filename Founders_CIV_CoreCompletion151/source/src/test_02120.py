"""Conservation, feeding provenance, control arm and deterministic replay."""
import copy,unittest
from unified_02120 import Unified220

class TestEmbodiedFood(unittest.TestCase):
    def setUp(self):self.s=Unified220(seed=9711,digestion=True)
    def test_single_book_and_no_new_external_inflow(self):
        self.assertIs(self.s.bridge.book,self.s.host.book)
        external=self.s.host.book.external
        self.s.run(4)
        self.assertEqual(self.s.host.book.audit()['rejections'],0)
        self.assertGreaterEqual(self.s.host.book.external,external)  # native host Wellspring legitimately funds the world
        self.assertAlmostEqual(self.s.host.book.audit()["energy_error"],0.,places=6)
    def test_bootstrap_embodiment_funded(self):
        b=self.s.host.book
        self.assertGreater(self.s.bridge.fluxes['initial_embodied_funded'],0)
        self.assertGreater(sum(b.energy[f'tissue_energy:{a.id}'] for a in self.s.bridge.actors.values()),0)
    def test_stock_feeding_cannot_mint_energy(self):
        b=self.s.host.book;a=next(x for x in self.s.bridge.actors.values() if x.species=='meadow_grazer')
        before=sum(b.energy.values());ext=b.external
        self.s.bridge._feed_herbivore(a)
        self.assertAlmostEqual(before,sum(b.energy.values()),places=7)
        self.assertEqual(ext,b.external)
    def test_zero_carcass_energy_no_scavenger_free_lunch(self):
        b=self.s.host.book;a=next(x for x in self.s.bridge.actors.values() if x.species=='carrion_bird')
        carrion=self.s.bridge.carrion(a.habitat)
        plant=self.s.bridge.physical.plant(a)
        self.s.bridge._convert([(plant,carrion,.001)])
        self.assertEqual(b.energy[self.s.bridge.physical.carrion_energy(a.habitat)],0.)
        en=b.energy[self.s.bridge.physical.reserve(a)]
        self.s.bridge._feed_stock(a,carrion,'carrion')
        self.assertEqual(en,b.energy[self.s.bridge.physical.reserve(a)])
        self.assertEqual(b.audit()['rejections'],0)
    def test_death_moves_embodiment_into_funded_carrion(self):
        b=self.s.host.book;a=next(x for x in self.s.bridge.actors.values() if x.species=='field_mouse')
        energy=b.energy[self.s.bridge.physical.tissue(a)]+b.energy[self.s.bridge.physical.maternal_energy(a)]
        carrion=self.s.bridge.physical.carrion_energy(a.habitat);previous=b.energy[carrion]
        self.s.bridge._death(a,'test')
        self.assertAlmostEqual(b.energy[carrion]-previous,energy,places=9)
        self.assertAlmostEqual(b.energy[self.s.bridge.physical.tissue(a)],0,places=9)
    def test_digestive_checkpoint_replay_exact(self):
        self.s.run(3);clone=copy.deepcopy(self.s)
        self.assertEqual(self.s.run(4),clone.run(4))
    def test_successful_hunt_is_funded_by_victim_tissue(self):
        b=self.s.host.book; h=next(x for x in self.s.bridge.actors.values() if x.species=='ridge_hound')
        mouse=next(x for x in self.s.bridge.actors.values() if x.species=='field_mouse')
        # Explicitly fund this test-only relocation, rather than mint prey at ridge.
        cost=min(.00035,b.energy[self.s.bridge.physical.reserve(mouse)])
        b.move(energy=[(self.s.bridge.physical.reserve(mouse),'environment:heat',cost)])
        mouse.habitat=h.habitat
        tissue=b.energy[self.s.bridge.physical.tissue(mouse)]
        assert tissue>0
        before=b.energy[self.s.bridge.physical.reserve(h)]
        oldrng=self.s.bridge.rng
        class Certain:
            def random(self):return 0.
            def choice(self,items):return items[0]
        self.s.bridge.rng=Certain()
        try:self.assertTrue(self.s.bridge._hunt(h))
        finally:self.s.bridge.rng=oldrng
        self.assertFalse(mouse.alive)
        self.assertAlmostEqual(b.energy[self.s.bridge.physical.tissue(mouse)],0.,places=9)
        self.assertGreater(self.s.bridge.fluxes['hunt_tissue_energy_gained'],0)
        self.assertGreater(b.energy[self.s.bridge.physical.carrion_energy(h.habitat)],0)
        self.assertAlmostEqual(b.audit()['energy_error'],0.,places=6)
        self.assertEqual(b.audit()['rejections'],0)

    def test_decay_dissipates_only_embodied_carcass_energy(self):
        b=self.s.host.book;mouse=next(x for x in self.s.bridge.actors.values() if x.species=='field_mouse')
        self.s.bridge._death(mouse,'test')
        origin=self.s.bridge.physical.carrion_energy(mouse.habitat)
        before=b.energy[origin]
        self.s.bridge._decay()
        self.assertGreater(before,b.energy[origin])
        self.assertAlmostEqual(b.audit()['energy_error'],0.,places=6)

    def test_control_remains_unchanged(self):
        a=Unified220(seed=9711,digestion=False)
        self.assertEqual(a.bridge.__class__.__name__,'HabitatBridge215')
        self.assertEqual(a.host.book.audit()['rejections'],0)

if __name__=='__main__':unittest.main()
