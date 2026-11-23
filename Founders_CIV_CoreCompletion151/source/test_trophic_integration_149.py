"""Cycle149 integration contract: real Book transfers and 13 functional species."""
import pickle
import unittest
from dataclasses import replace
from trophic_integration_149 import UnifiedTrophicIntegration149
from ecoregulation_148 import UnifiedEcoRegulation148
from core_physiology_v2 import PREY, PROFILES
from species_traits_143 import BLUEPRINTS, FIELDS
from trophic_roles_146 import CARNIVORE_ROLES, PLANT_EATER_ROLES
from trophic_guilds_cycle138 import _temporary_diet_registry, ANTS

class TrophicIntegration149Tests(unittest.TestCase):
    def setUp(self):
        self.sim=UnifiedTrophicIntegration149(seed=100001)
        self.br=self.sim.bridge;self.book=self.sim.host.book
        self.ctx=_temporary_diet_registry();self.ctx.__enter__()

    def tearDown(self):self.ctx.__exit__(None,None,None)

    def animal(self, species, sex=None):
        return next(a for a in self.br.actors.values() if a.alive and
                    a.species==species and (sex is None or a.sex==sex))

    def test_01_all_species_active_traits_niches(self):
        self.assertEqual(len(BLUEPRINTS),13)
        self.assertEqual(len(set(a.species for a in self.br.actors.values())),13)
        self.assertEqual(set(PROFILES),set(BLUEPRINTS))
        self.assertEqual(set(CARNIVORE_ROLES)|set(PLANT_EATER_ROLES)|{ANTS},set(BLUEPRINTS))
        for a in self.br.actors.values():
            p=self.br._trait(a)
            self.assertTrue(all(getattr(p,f)>0 for f in FIELDS))
            self.assertIn(a.species,PROFILES)
        self.assertIs(self.book,self.br.book)
        self.assertIs(self.book,self.br.tree.book)
        self.assertEqual(len(self.sim.host.sim.founders.people),100)

    def test_02_trait_causes_metabolic_difference(self):
        for species in BLUEPRINTS:
            a=self.animal(species)
            initial=self.br.phenotypes[a.id]
            old=self.br._maintenance_demand(a)
            alternate=replace(initial,basal=min(1.40,initial.basal*1.04))
            self.br.phenotypes[a.id]=alternate
            self.assertGreater(self.br._maintenance_demand(a),old)
            self.br.phenotypes[a.id]=initial

    def test_03_kill_uses_real_prey_fuel_once(self):
        fox=self.animal('red_fox'); habitat=fox.habitat
        victim=next(p for p in self.br.actors.values()
                    if p.alive and p.habitat==habitat and p.species in PREY['red_fox'])
        self.br.positions[victim.id]=self.br._pos(fox)
        initial_fuel=self.book.energy[self.br.physical.reserve(victim)]+self.book.energy[self.br._short(victim)]
        energy_total=self.book.audit()['energy_total']
        before=self.book.energy[self.br._gut_energy(fox)]
        self.br.rng.random=lambda:0.0
        self.assertTrue(self.br._hunt(fox))
        self.assertFalse(victim.alive)
        kill=next(e for e in reversed(self.br.events) if e['event']=='predation')
        predicted=initial_fuel*kill['consumed']/kill['prey_mass']
        actual=self.br.integration149_metrics['previously_stranded_prey_fuel_to_gut']
        self.assertAlmostEqual(actual,predicted,places=9)
        self.assertGreater(self.book.energy[self.br._gut_energy(fox)],before)
        self.assertAlmostEqual(self.book.audit()['energy_total'],energy_total,places=5)
        self.assertEqual(self.book.audit()['rejections'],0)
        self.assertGreater(self.br.integration149_metrics['carcass_mass_localized'],0)

    def test_04_carcass_stays_where_prey_died_and_is_edible(self):
        fox=self.animal('red_fox'); victim=next(p for p in self.br.actors.values()
                   if p.alive and p.habitat==fox.habitat and p.species in PREY['red_fox'])
        location=self.br._pos(fox);self.br.positions[victim.id]=location
        self.br.rng.random=lambda:0.0
        self.assertTrue(self.br._hunt(fox))
        self.assertGreater(self.br._carcass_patches149.get(location,0.),0)
        # The nearby second fox can actually ingest the remaining material.
        second=next(a for a in self.br.actors.values() if a.alive and a.species=='red_fox' and a.id!=fox.id)
        second.habitat=fox.habitat;self.br.positions[second.id]=location
        gut=self.book.mass[self.br.physical.gut(second)]
        self.assertTrue(self.br._scavenge(second))
        self.assertGreater(self.book.mass[self.br.physical.gut(second)],gut)
        self.assertEqual(self.book.audit()['rejections'],0)

    def test_05_carcass_conservation_after_refresh(self):
        fox=self.animal('red_fox');victim=next(p for p in self.br.actors.values()
                     if p.alive and p.habitat==fox.habitat and p.species in PREY['red_fox'])
        location=self.br._pos(fox);self.br.positions[victim.id]=location
        self.br.rng.random=lambda:0.0;self.br._hunt(fox)
        source=self.br.carrion(fox.habitat)
        credited=self.br._carcass_patches149[location]
        self.br.day+=1;self.br._refresh_quota()
        self.assertLessEqual(sum(v for (s,*_),v in self.br._cell_quota.items() if s==source),self.book.mass[source]+1e-9)
        self.assertGreaterEqual(self.br._cell_quota[(source,*location)],credited-1e-9)
        self.assertEqual(self.book.audit()['rejections'],0)

    def test_06_no_predation_creates_no_kill_reward(self):
        self.br.predation_enabled=False
        before=self.book.audit()['energy_total']
        self.br._hunt(self.animal('ridge_hound'))
        self.assertEqual(self.br.integration149_metrics['kills_with_conserved_reward'],0)
        self.assertAlmostEqual(self.book.audit()['energy_total'],before,places=5)

    def test_07_all_off_bitwise_matches_core148(self):
        base=UnifiedEcoRegulation148(seed=100003)
        off=UnifiedTrophicIntegration149(seed=100003,trophic_integration=False)
        for _ in range(9):base.step();off.step()
        self.assertEqual(dict(base.host.book.mass),dict(off.host.book.mass))
        self.assertEqual(dict(base.host.book.energy),dict(off.host.book.energy))
        self.assertEqual([(a.id,a.alive,a.age,a.habitat) for a in base.bridge.actors.values()],
                         [(a.id,a.alive,a.age,a.habitat) for a in off.bridge.actors.values()])

    def test_08_checkpoint_replay_includes_patches_and_traits(self):
        self.sim.run(7)
        clone=pickle.loads(pickle.dumps(self.sim))
        self.sim.run(7);clone.run(7)
        self.assertEqual(dict(self.sim.host.book.mass),dict(clone.host.book.mass))
        self.assertEqual(dict(self.sim.host.book.energy),dict(clone.host.book.energy))
        self.assertEqual(self.sim.bridge._carcass_patches149,clone.bridge._carcass_patches149)
        self.assertEqual(self.sim.bridge.phenotypes,clone.bridge.phenotypes)
        self.assertEqual(dict(self.sim.bridge.integration149_metrics),dict(clone.bridge.integration149_metrics))

    def test_09_isolated_kill_nutrition_ablation(self):
        isolated=UnifiedTrophicIntegration149(seed=100001,
                   kill_nutrition=False,carcass_locality=True,
                   carcass_preference=False)
        br=isolated.bridge
        with _temporary_diet_registry():
            fox=next(a for a in br.actors.values() if a.species=='red_fox')
            prey=next(a for a in br.actors.values() if a.alive and
                      a.habitat==fox.habitat and a.species in PREY['red_fox'])
            br.positions[prey.id]=br._pos(fox)
            br.rng.random=lambda:0.0
            self.assertTrue(br._hunt(fox))
            self.assertFalse(prey.alive)
            self.assertEqual(br.integration149_metrics['previously_stranded_prey_fuel_to_gut'],0.)
            self.assertGreater(br.integration149_metrics['carcass_mass_localized'],0.)
            self.assertEqual(isolated.host.book.audit()['rejections'],0)

    def test_10_five_disjoint_species_feeding_roles(self):
        # Each species has exactly one primary functional route, with shrews
        # accessing colony workers and carrion birds scavenging real carrion.
        self.assertEqual(len(CARNIVORE_ROLES),5)
        self.assertEqual(len(PLANT_EATER_ROLES),7)
        self.assertNotIn(ANTS,CARNIVORE_ROLES)
        self.assertNotIn(ANTS,PLANT_EATER_ROLES)
        self.assertEqual(set(CARNIVORE_ROLES)&set(PLANT_EATER_ROLES),set())

    def test_11_normal_multiday_sim_preserves_accounting(self):
        self.sim.run(20)
        self.assertEqual(self.book.audit()['rejections'],0)
        self.assertTrue(self.br.audit_species_contracts())
        self.assertGreater(self.br.integration149_metrics['kills_with_conserved_reward'],0)
        self.assertEqual(self.br.tree.state,'active')

    def test_12_every_plant_eater_can_ingest_actual_plant_energy(self):
        # Includes both megaherbivores and every fast-breeding prey herbivore.
        for species in PLANT_EATER_ROLES:
            animal=self.animal(species)
            gut=self.br.physical.gut(animal)
            source=self.br.tree.acct('plant',animal.habitat)
            before=self.book.energy[self.br._gut_energy(animal)]
            self.assertTrue(self.br._feed_stock(animal,source,'species_contract',dt=1.),species)
            self.assertGreater(self.book.energy[self.br._gut_energy(animal)],before,species)
            self.assertGreater(self.book.mass[gut],0,species)
        self.assertEqual(self.book.audit()['rejections'],0)

    def test_13_shrew_worker_energy_enters_gut_not_reserve(self):
        ant=self.animal('ant_colony')
        shrew=next(x for x in self.br.actors.values() if x.alive and
                   x.species=='insectivore_shrew' and x.habitat==ant.habitat)
        self.br.positions[shrew.id]=self.br._pos(ant)
        reserve=self.book.energy[self.br.physical.reserve(shrew)]
        gut=self.book.energy[self.br._gut_energy(shrew)]
        ant_mass=self.book.mass[self.br.physical.live(ant)]
        audit=self.book.audit()
        self.assertTrue(self.br._ant_worker_take(shrew))
        self.assertAlmostEqual(self.book.energy[self.br.physical.reserve(shrew)],reserve)
        self.assertGreater(self.book.energy[self.br._gut_energy(shrew)],gut)
        self.assertLess(self.book.mass[self.br.physical.live(ant)],ant_mass)
        self.assertAlmostEqual(self.book.audit()['mass_total'],audit['mass_total'],places=7)
        self.assertAlmostEqual(self.book.audit()['energy_total'],audit['energy_total'],places=5)
        self.assertEqual(self.book.audit()['rejections'],0)

    def test_14_every_meat_eater_can_ingest_book_funded_carrion(self):
        # Carcasses come from real existing animal body and tissue stocks, not
        # a synthetic caloric bonus or a habitat energy mint.
        for species in CARNIVORE_ROLES:
            hunter=self.animal(species)
            donor=next(a for a in self.br.actors.values() if a.alive and
                a.id!=hunter.id and a.habitat==hunter.habitat and
                self.book.mass[self.br.physical.live(a)]>.02)
            body_key=self.br.physical.live(donor)
            body_mass=self.book.mass[body_key]
            q=min(.02,body_mass*.08)
            energy_key=self.br.physical.tissue(donor)
            e=self.book.energy[energy_key]*q/body_mass
            source=self.br.carrion(hunter.habitat)
            self.br.physical.convert([(body_key,source,q)])
            self.book.move(energy=[(energy_key,
                self.br.physical.carrion_energy(hunter.habitat),e)])
            self.br._quota_day=-1
            self.br._refresh_quota()
            spots=[(v,k) for k,v in self.br._cell_quota.items()
                if k[0]==source and k[1]==hunter.habitat]
            location=max(spots,key=lambda pair:pair[0])[1][1:]
            self.br.positions[hunter.id]=location
            before=self.book.energy[self.br._gut_energy(hunter)]
            self.assertTrue(self.br._feed_stock(hunter,source,
                            'role_contract_149',dt=1.),species)
            self.assertGreater(self.book.energy[self.br._gut_energy(hunter)],before,species)
        self.assertEqual(self.book.audit()['rejections'],0)

if __name__=='__main__':unittest.main()
