"""Focused v0.21.14 tests; v0.21.13 tests run unchanged separately."""
import os,tempfile,unittest
from unified_02114 import Unified214
from habitat_bridge_02114 import HabitatBridge214

class FixedRandom:
    def random(self):return 0.
    def choice(self,seq):return seq[0]

class MigrationTests(unittest.TestCase):
    def test_one_clock_one_book_unique_actors(self):
        sim=Unified214(seed=9711)
        sim.run(2)
        self.assertIs(sim.host.book,sim.bridge.book)
        self.assertIs(sim.host.book,sim.host.sim.book)
        self.assertEqual(sim.days,sim.host.sim.tick-sim.host.bootstrap_tick)
        self.assertEqual(len(sim.host.sim.founders.people),100)
        c=sim.bridge.census()
        self.assertEqual(c['bridge_total']+c['world023_residents'],c['combined_unique'])
        self.assertEqual(c['distinct_biological_schedulers'],2)

    def test_predator_encounters_previously_inaccessible_prey(self):
        sim=Unified214(seed=9711)
        a=next(a for a in sim.bridge.actors.values() if a.species=='ridge_hound')
        old=sim.host.book.energy[f'animal:{a.id}']
        self.assertEqual(a.habitat,'ridge')
        self.assertTrue(sim.bridge._migrate(a))
        self.assertEqual(a.habitat,'grassland')
        self.assertAlmostEqual(old-sim.host.book.energy[f'animal:{a.id}'],sim.bridge.TRAVEL_COST)
        self.assertTrue(any(e['event']=='migration' and e['reason']=='prey_encounter'
                            for e in sim.bridge.events))
        sim.host.book.audit()

    def test_hunting_carcass_scavenging_and_decomposition(self):
        sim=Unified214(seed=9711)
        b=sim.bridge
        predator=next(a for a in b.actors.values() if a.species=='ridge_hound')
        self.assertTrue(b._migrate(predator))
        b.rng=FixedRandom()
        prey_mass=sum(sim.host.book.mass[f'live:{a.id}'] for a in b.actors.values()
                      if a.alive and a.species in ('field_mouse','meadow_grazer'))
        self.assertTrue(b._hunt(predator))
        prey_mass_after=sum(sim.host.book.mass[f'live:{a.id}'] for a in b.actors.values()
                            if a.alive and a.species in ('field_mouse','meadow_grazer'))
        self.assertLess(prey_mass_after,prey_mass)
        self.assertGreater(sim.host.book.mass[b.carrion('grassland')],0)
        bird=next(a for a in b.actors.values() if a.species=='carrion_bird')
        # Explicitly stage this isolated feeding unit test in grassland.
        bird.habitat='grassland'
        carrion_before=sim.host.book.mass[b.carrion('grassland')]
        self.assertTrue(b._feed_scavenger(bird))
        self.assertLess(sim.host.book.mass[b.carrion('grassland')],carrion_before)
        det_before=sim.host.book.mass[b.tree.acct('detritus','grassland')]
        b._decay()
        self.assertGreater(sim.host.book.mass[b.tree.acct('detritus','grassland')],det_before)
        sim.host.book.audit();b._check_registry()

    def test_checkpoint_replay(self):
        sim=Unified214(seed=9713)
        sim.run(4)
        with tempfile.TemporaryDirectory() as tmp:
            filename=os.path.join(tmp,'resume.pkl')
            sim.save(filename)
            resumed=Unified214.load(filename)
            self.assertEqual(resumed.run(6),sim.run(6))

    def test_forced_collapse_remnants(self):
        sim=Unified214(seed=9714)
        sim.bridge.tree.collapse('forced_test')
        self.assertEqual(sim.host.book.energy[sim.bridge.tree.acct('sun','forest')],0)
        sim.bridge.step(1)
        self.assertEqual(sum(sim.bridge.report().values()),0)
        self.assertEqual(sim.host.book.audit()['rejections'],0)
        self.assertEqual(len([a for a in sim.bridge.actors.values() if a.alive]),0)
        for a in sim.bridge.actors.values():
            self.assertAlmostEqual(sim.host.book.mass[f'live:{a.id}'],0)
        self.assertGreater(sim.host.book.mass[f'remnant:tree:{sim.bridge.tree.id}:ridge'],0)

if __name__=='__main__':unittest.main()
