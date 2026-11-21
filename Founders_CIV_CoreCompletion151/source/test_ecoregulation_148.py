"""Cycle148: physical tracking, local mate access, controls, replay."""
import pickle
import unittest
from ecoregulation_148 import UnifiedEcoRegulation148
from fuel_flex_147 import UnifiedFuelFlex147
from core_physiology_v2 import PREY
from trophic_guilds_cycle138 import _temporary_diet_registry

class EcoRegulation148Tests(unittest.TestCase):
    def setUp(self):
        self.sim=UnifiedEcoRegulation148(seed=100001)
        self.br=self.sim.bridge
        self.book=self.br.book
        self._diet_ctx=_temporary_diet_registry()
        self._diet_ctx.__enter__()

    def tearDown(self):
        self._diet_ctx.__exit__(None,None,None)

    def hound(self):
        return next(a for a in self.br.actors.values() if a.species=='ridge_hound' and a.alive)

    def fox(self):
        return next(a for a in self.br.actors.values() if a.species=='red_fox' and a.alive)

    def test_01_single_book_founders_and_species(self):
        self.assertIs(self.book,self.sim.host.book)
        self.assertIs(self.book,self.br.tree.book)
        self.assertEqual(len(self.sim.host.sim.founders.people),100)
        self.assertEqual(len({a.species for a in self.br.actors.values()}),13)
        self.assertEqual(self.book.audit()['rejections'],0)

    def test_02_tracking_is_physical_one_cell_and_book_paid(self):
        h=self.fox()
        here=(h.habitat,0,0)
        self.br.positions[h.id]=here
        candidates=[p for p in self.br.actors.values()
            if p.alive and p.habitat==h.habitat and p.species in PREY[h.species]]
        self.assertTrue(candidates)
        for p in candidates:self.br.positions[p.id]=(h.habitat,7,7)
        self.br.positions[candidates[0].id]=(h.habitat,0,2)
        audit_before=self.book.audit()['energy_total']
        heat_before=self.book.energy['environment:heat']
        self.assertTrue(self.br._track_local_prey(h))
        self.assertEqual(self.br._pos(h),(h.habitat,0,1))
        self.assertGreater(self.book.energy['environment:heat'],heat_before)
        self.assertAlmostEqual(self.book.audit()['energy_total'],audit_before,places=5)
        self.assertEqual(self.book.audit()['rejections'],0)

    def test_03_tracking_has_no_omniscient_distant_prey(self):
        h=self.fox();self.br.positions[h.id]=(h.habitat,0,0)
        for p in self.br.actors.values():
            if p.alive and p.habitat==h.habitat and p.species in PREY[h.species]:
                self.br.positions[p.id]=(h.habitat,7,7)
        before=self.book.audit()['energy_total']
        local=self.br._track_local_prey(h)
        self.assertIsNone(local)
        self.assertEqual(self.br._pos(h),(h.habitat,0,0))
        self.assertAlmostEqual(self.book.audit()['energy_total'],before,places=5)

    def test_04_tracking_deferred_strike(self):
        h=self.hound();h.condition=1.
        self.br._state(h).last_tracking_step=(self.br.day,0)
        self.br._substep_index=0
        before=sum(x.alive for x in self.br.actors.values())
        self.br._hunt(h)
        self.assertEqual(sum(x.alive for x in self.br.actors.values()),before)
        self.assertGreaterEqual(self.br.ecoregulation_metrics['strike_deferred_after_tracking'],1)

    def test_05_local_mate_cue_needs_neighbor(self):
        b=self.br
        animal=next(a for a in b.actors.values() if a.species=='meadow_grazer' and a.stage=='adult')
        neighbor=next(iter(b.tree.habitats[animal.habitat].neighbors))
        for p in b.actors.values():
            if p.species==animal.species and p.id!=animal.id and p.sex!=animal.sex and p.stage=='adult':
                p.habitat=neighbor
        options=b._local_mate_habitats(animal)
        self.assertIn(neighbor,options)
        self.assertNotIn(animal.habitat,options)

    def test_05b_mate_search_migration_is_paid_and_never_guarantees_birth(self):
        from unittest.mock import patch
        b=self.br
        individual=next(a for a in b.actors.values() if a.species=='meadow_grazer' and a.stage=='adult')
        target=next(iter(b.tree.habitats[individual.habitat].neighbors))
        for p in b.actors.values():
            if p.species==individual.species and p.id!=individual.id and p.sex!=individual.sex and p.stage=='adult':
                p.habitat=target
        self.assertIn(target,b._local_mate_habitats(individual))
        b._state(individual).fatigue=0.
        before_heat=self.book.energy['environment:heat']
        before_energy=self.book.audit()['energy_total']
        before_births=len(b.actors)
        with patch.object(b.rng,'random',return_value=0.):
            moved=b._migrate(individual,'search')
        self.assertTrue(moved)
        self.assertEqual(individual.habitat,target)
        self.assertGreater(self.book.energy['environment:heat'],before_heat)
        self.assertEqual(len(b.actors),before_births)
        self.assertAlmostEqual(self.book.audit()['energy_total'],before_energy,places=5)

    def test_06_off_is_exact_core147_book_and_actor_state(self):
        old=UnifiedFuelFlex147(seed=100002)
        off=UnifiedEcoRegulation148(seed=100002,local_tracking=False,mate_search=False)
        for _ in range(6):
            old.step();off.step()
        self.assertEqual(dict(old.host.book.mass),dict(off.host.book.mass))
        self.assertEqual(dict(old.host.book.energy),dict(off.host.book.energy))
        self.assertEqual([(a.id,a.alive,a.habitat,a.age) for a in old.bridge.actors.values()],
                         [(a.id,a.alive,a.habitat,a.age) for a in off.bridge.actors.values()])

    def test_07_checkpoint_replay(self):
        self.sim.run(6)
        cloned=pickle.loads(pickle.dumps(self.sim))
        self.sim.run(6);cloned.run(6)
        self.assertEqual(dict(self.sim.host.book.mass),dict(cloned.host.book.mass))
        self.assertEqual(dict(self.sim.host.book.energy),dict(cloned.host.book.energy))
        self.assertEqual(dict(self.br.ecoregulation_metrics),dict(cloned.bridge.ecoregulation_metrics))
        self.assertEqual({a.id:(a.alive,a.habitat,a.age) for a in self.br.actors.values()},
                         {a.id:(a.alive,a.habitat,a.age) for a in cloned.bridge.actors.values()})

    def test_08_real_tracking_occurs(self):
        self.sim.run(10)
        self.assertGreater(self.br.ecoregulation_metrics['paid_local_tracking_steps'],0)
        self.assertEqual(self.book.audit()['rejections'],0)

    def test_09_no_actor_time_wallet(self):
        a=self.hound()
        before=dict(self.book.energy)
        self.br._choose(a)
        for key in set(before)|set(self.book.energy):
            self.assertAlmostEqual(before.get(key,0.),self.book.energy.get(key,0.),places=12)
        self.assertFalse(hasattr(a,'time_wallet'))

if __name__=='__main__':unittest.main()
