"""Cycle150 reproducible cleanup verification, no synthetic survival rewards."""
import pickle
import unittest
from unittest.mock import patch
from integration_cleanup_150 import UnifiedCleanup150
from trophic_integration_149 import UnifiedTrophicIntegration149, TrophicIntegrationBridge149
from core_physiology_v2 import PREY
from trophic_roles_146 import CARNIVORE_ROLES
from trophic_guilds_cycle138 import _temporary_diet_registry


class Cleanup150Tests(unittest.TestCase):
    def setUp(self):
        self.sim = UnifiedCleanup150(seed=100001)
        self.br = self.sim.bridge
        self.b = self.br.book
        self.ctx = _temporary_diet_registry()
        self.ctx.__enter__()
    def tearDown(self):
        self.ctx.__exit__(None, None, None)

    def kill_fox_prey(self):
        fox = next(a for a in self.br.actors.values() if a.alive and a.species=='red_fox')
        prey = next(a for a in self.br.actors.values() if a.alive and
                    a.habitat==fox.habitat and a.species in PREY['red_fox'])
        self.br.positions[prey.id] = self.br._pos(fox)
        self.br.rng.random = lambda: 0.0
        assert self.br._hunt(fox)
        assert not prey.alive
        return fox, prey

    def test_01_kill_binds_carcass_mass_and_embodied_energy(self):
        fox, prey = self.kill_fox_prey()
        loc = self.br._pos(prey)
        self.assertGreater(self.br._carcass_patches149[loc], 0.)
        self.assertGreater(self.br._carcass_energy_patches150[loc], 0.)
        self.assertLessEqual(self.br._carcass_energy_patches150[loc],
            self.b.energy[self.br.physical.carrion_energy(fox.habitat)] + 1e-10)
        self.assertEqual(self.b.audit()['rejections'], 0)

    def test_02_local_meal_uses_local_energy_density(self):
        fox, prey = self.kill_fox_prey()
        loc = self.br._pos(fox)
        patch_mass = self.br._carcass_patches149[loc]
        patch_energy = self.br._carcass_energy_patches150[loc]
        small = min(.0001, patch_mass*.1)
        before = self.br._carcass_energy_offer(fox, small)
        self.assertAlmostEqual(before, small*patch_energy/patch_mass, places=10)
        # Move legitimate mass+energy from another living animal into a
        # separate remote carcass. A global-average model wrongly changes
        # local nutrition when remote carcasses have different densities.
        donor = next(a for a in self.br.actors.values() if a.alive and
            a.id!=fox.id and a.habitat==fox.habitat and self.b.mass[self.br.physical.live(a)]>.02)
        body=self.b.mass[self.br.physical.live(donor)]
        q=min(.01, body*.08)
        energy=self.b.energy[self.br.physical.tissue(donor)]*q/body
        source=self.br.carrion(fox.habitat)
        self.br.physical.convert([(self.br.physical.live(donor),source,q)])
        self.b.move(energy=[(self.br.physical.tissue(donor),
                             self.br.physical.carrion_energy(fox.habitat),energy)])
        z=self.br.grid_size
        remote=(loc[0],(loc[1]+z//2)%z,(loc[2]+z//2)%z)
        self.br._carcass_patches149[remote]=self.br._carcass_patches149.get(remote,0.)+q
        self.br._carcass_energy_patches150[remote]=self.br._carcass_energy_patches150.get(remote,0.)+energy
        self.br._cell_quota[(source,*remote)]=self.br._cell_quota.get((source,*remote),0.)+q
        after=self.br._carcass_energy_offer(fox,small)
        self.assertAlmostEqual(before,after,places=10)
        self.assertEqual(self.b.audit()['rejections'],0)

    def test_03_feeding_debits_paired_local_carcass_and_gut(self):
        fox, prey = self.kill_fox_prey()
        loc=self.br._pos(prey)
        second=next(a for a in self.br.actors.values() if a.alive and a.species=='red_fox' and a.id!=fox.id)
        second.habitat=fox.habitat
        self.br.positions[second.id]=loc
        m0=self.br._carcass_patches149[loc]
        e0=self.br._carcass_energy_patches150[loc]
        gut_energy0=self.b.energy[self.br._gut_energy(second)]
        self.assertTrue(self.br._scavenge(second))
        self.assertLess(self.br._carcass_patches149[loc],m0)
        self.assertLess(self.br._carcass_energy_patches150[loc],e0)
        self.assertGreater(self.b.energy[self.br._gut_energy(second)],gut_energy0)
        self.assertEqual(self.b.audit()['rejections'],0)

    def test_04_full_gut_stops_unproductive_hunt_intent(self):
        fox=next(a for a in self.br.actors.values() if a.alive and a.species=='red_fox')
        cap=CARNIVORE_ROLES['red_fox'].stomach_fraction*self.br._bodymass(fox)
        gut=self.br.physical.gut(fox)
        # Use existing living tissue in the Book to simulate an already filled
        # stomach; never seed or mint gut mass in a running world.
        donor=max((a for a in self.br.actors.values() if a.alive and
                   a.id!=fox.id and a.habitat==fox.habitat),
                  key=lambda a:self.b.mass[self.br.physical.live(a)])
        source=self.br.physical.live(donor)
        stock=self.b.mass[source]
        self.assertGreater(stock,cap*.75)
        q=cap*.73
        embodied=self.b.energy[self.br.physical.tissue(donor)]*q/stock
        self.br.physical.convert([(source,gut,q)])
        self.b.move(energy=[(self.br.physical.tissue(donor),
                             self.br._gut_energy(fox),embodied)])
        with patch.object(TrophicIntegrationBridge149,'_choose',return_value=('feed',.99,False)):
            action,hunger,danger=self.br._choose(fox)
        self.assertEqual(action,'rest')
        self.assertEqual(self.br.cleanup150_metrics['full_gut_rest_decisions'],1)
        self.b.audit()

    def test_05_replay_preserves_local_energy_and_traits(self):
        self.sim.run(9)
        clone=pickle.loads(pickle.dumps(self.sim))
        self.sim.run(7)
        clone.run(7)
        self.assertEqual(dict(self.sim.host.book.mass),dict(clone.host.book.mass))
        self.assertEqual(dict(self.sim.host.book.energy),dict(clone.host.book.energy))
        self.assertEqual(self.sim.bridge._carcass_energy_patches150,clone.bridge._carcass_energy_patches150)
        self.assertEqual(self.sim.bridge.phenotypes,clone.bridge.phenotypes)

    def test_06_disabled_cleanup_is_bitwise_core149(self):
        old=UnifiedTrophicIntegration149(seed=100003)
        off=UnifiedCleanup150(seed=100003,cleanup150=False)
        for _ in range(10):old.step();off.step()
        self.assertEqual(dict(old.host.book.mass),dict(off.host.book.mass))
        self.assertEqual(dict(old.host.book.energy),dict(off.host.book.energy))
        self.assertEqual([(x.id,x.alive,x.habitat) for x in old.bridge.actors.values()],
                         [(x.id,x.alive,x.habitat) for x in off.bridge.actors.values()])

    def test_07_no_duplicate_carcass_energy_under_refresh(self):
        fox, prey=self.kill_fox_prey()
        h=fox.habitat
        source=self.br.carrion(h)
        self.br.day+=1
        self.br._refresh_quota()
        self.assertLessEqual(sum(v for k,v in self.br._carcass_energy_patches150.items() if k[0]==h),
            self.b.energy[self.br.physical.carrion_energy(h)]+1e-9)
        self.assertLessEqual(sum(v for k,v in self.br._cell_quota.items() if k[0]==source),
            self.b.mass[source]+1e-9)
        self.assertEqual(self.b.audit()['rejections'],0)

if __name__=='__main__':unittest.main()
