"""Cycle146: physically funded niche ecology and predator-prey validation."""
import pickle
import unittest
from core_completion_145 import UnifiedCoreCompletion145
from core_completion_146 import UnifiedCoreCompletion146, TrophicInventory146
from trophic_roles_146 import CARNIVORE_ROLES
from species_traits_143 import BLUEPRINTS
from trophic_guilds_cycle138 import GUILD_PREDATORS

class Cycle146Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim=UnifiedCoreCompletion146(seed=100001)

    def setUp(self):
        self.sim=pickle.loads(pickle.dumps(type(self).sim))
        self.br=self.sim.bridge; self.b=self.sim.host.book

    def animal(self,name,sex=None):
        return next(a for a in self.br.actors.values() if a.species==name and (sex is None or a.sex==sex))

    def deposit_carrion(self,habitat,amount=.005):
        prey=next(a for a in self.br.actors.values() if a.species=='burrow_rabbit' and a.habitat==habitat)
        original=self.b.mass[self.br.physical.live(prey)]
        q=min(amount,original*.12)
        self.br.physical.convert([(self.br.physical.live(prey),self.br.carrion(habitat),q)])
        source=self.br.physical.tissue(prey)
        e=self.b.energy[source]*q/max(original,1e-12)
        if e:self.b.move(energy=[(source,self.br.physical.carrion_energy(habitat),e)])
        return q

    def test01_shared_book_13_trait_blueprints(self):
        self.assertIs(self.b,self.br.book)
        self.assertIs(self.b,self.br.tree.book)
        self.assertEqual(len(self.sim.host.sim.founders.people),100)
        self.assertEqual(len(BLUEPRINTS),13)
        self.assertEqual(set(self.br.phenotypes),set(self.br.actors))
        self.assertEqual(self.b.audit()['rejections'],0)

    def test02_real_carrion_density_tracks_book_energy(self):
        fox=self.animal('red_fox')
        self.deposit_carrion(fox.habitat)
        lot=self.br.lots.carrion(fox.habitat)
        self.assertIsInstance(self.br.lots,TrophicInventory146)
        ratio=self.b.energy[lot.energy_account]/self.b.mass[lot.mass_account]
        self.assertAlmostEqual(lot.nominal_density,ratio,places=9)
        self.assertGreater(self.br.lots.available_mass(lot),0)

    def test03_meat_larger_meal_without_instant_reserve_mint(self):
        fox=self.animal('red_fox')
        self.deposit_carrion(fox.habitat)
        gut=self.br.physical.gut(fox)
        previous=self.b.mass[gut]; reserve=self.b.energy[self.br.physical.reserve(fox)]
        before=self.b.audit()['energy_total']
        self.assertTrue(self.br._feed_stock(fox,self.br.carrion(fox.habitat),'scavenge',dt=1.))
        self.assertGreater(self.b.mass[gut],previous)
        self.assertAlmostEqual(self.b.energy[self.br.physical.reserve(fox)],reserve)
        self.assertAlmostEqual(self.b.audit()['energy_total'],before)
        self.assertEqual(self.b.audit()['rejections'],0)

    def test04_diet_quality_is_not_new_energy(self):
        fox=self.animal('red_fox'); self.deposit_carrion(fox.habitat)
        self.br._feed_stock(fox,self.br.carrion(fox.habitat),'scavenge',dt=1.)
        state=self.br._state(fox)
        self.assertAlmostEqual(state.gut_quality_weight/state.gut_energy_weight,
                               CARNIVORE_ROLES['red_fox'].meat_digestibility)
        e=self.b.audit()['energy_total']
        self.br._digest(fox,dt=.5)
        self.assertAlmostEqual(self.b.audit()['energy_total'],e)
        self.assertGreater(self.br.trophic_metrics['carnivore_digestions'],0)

    def test05_satiation_blocks_redundant_predation(self):
        h=self.animal('ridge_hound')
        capacity=CARNIVORE_ROLES['ridge_hound'].stomach_fraction*self.br._bodymass(h)
        q=max(0.,capacity*.85-self.b.mass[self.br.physical.gut(h)])
        if q:
            source=self.br.physical.plant(h)
            self.br.physical.convert([(source,self.br.physical.gut(h),q)])
        before=self.br.physiology_metrics['kills']
        self.assertFalse(self.br._hunt(h))
        self.assertEqual(self.br.physiology_metrics['kills'],before)
        self.assertGreater(self.br.trophic_metrics['satiated_hunt_deferred'],0)
        self.assertEqual(self.b.audit()['rejections'],0)

    def test06_hunting_disabled_preserves_predation_control(self):
        self.br.predation_enabled=False
        h=self.animal('ridge_hound')
        before=self.br.physiology_metrics['kills']
        self.assertFalse(self.br._hunt(h))
        self.assertEqual(self.br.physiology_metrics['kills'],before)

    def test07_carnivore_can_use_killed_animal_carcass(self):
        fox=self.animal('red_fox');self.deposit_carrion(fox.habitat)
        # Place the hunter in the highest-resource microcell as a controlled
        # spatial fixture; it may not teleport from an unrelated cell.
        self.br._refresh_quota()
        h=fox.habitat;source=self.br.carrion(h)
        best=max([(v,k) for k,v in self.br._cell_quota.items()
                  if k[0]==source and k[1]==h],key=lambda x:x[0])[1]
        self.br.positions[fox.id]=(best[1],best[2],best[3])
        self.assertTrue(self.br._scavenge(fox))
        self.assertGreater(self.br.trophic_metrics['scavenge_meals'],0)
        self.assertEqual(self.b.audit()['rejections'],0)

    def test08_trait_variation_affects_full_species_ecology(self):
        for a in self.br.actors.values():
            p=self.br._trait(a)
            self.assertTrue(all(getattr(p,key)>0 for key in p.asdict()))
        self.assertEqual(set(CARNIVORE_ROLES),
                         {'ridge_hound','red_fox','golden_jackal','insectivore_shrew','carrion_bird'})
        for species in CARNIVORE_ROLES:
            self.assertIn(species,BLUEPRINTS)
        for predator in ('ridge_hound','red_fox','golden_jackal'):
            self.assertGreater(len(GUILD_PREDATORS[predator]),1)

    def test09_exact_replay_book_trait_and_trophic_state(self):
        self.sim.run(5)
        clone=pickle.loads(pickle.dumps(self.sim))
        self.sim.run(5);clone.run(5)
        self.assertEqual(dict(self.sim.host.book.mass),dict(clone.host.book.mass))
        self.assertEqual(dict(self.sim.host.book.energy),dict(clone.host.book.energy))
        self.assertEqual(self.sim.bridge.phenotypes,clone.bridge.phenotypes)
        self.assertEqual(dict(self.sim.bridge.trophic_metrics),dict(clone.bridge.trophic_metrics))
        self.assertEqual(self.b.audit()['rejections'],0)

    def test10_all_features_off_reproduces_core145_demography(self):
        control=UnifiedCoreCompletion145(seed=100002)
        off=UnifiedCoreCompletion146(seed=100002,trophic_diet=False,
                                     trophic_hunting=False,trophic_provisioning=False)
        control.run(6);off.run(6)
        self.assertEqual([(a.id,a.alive,a.age,a.habitat) for a in control.bridge.actors.values()],
                         [(a.id,a.alive,a.age,a.habitat) for a in off.bridge.actors.values()])
        self.assertEqual(dict(control.host.book.mass),dict(off.host.book.mass))
        self.assertEqual(dict(control.host.book.energy),dict(off.host.book.energy))

    def test11_roles_have_no_guaranteed_population_floor(self):
        a=self.animal('red_fox')
        self.br._death(a,'physiological_failure')
        self.assertFalse(a.alive)
        self.assertEqual(self.b.audit()['rejections'],0)

    def test12_prey_and_native_schedulers_remain_distinct(self):
        self.assertIsNot(self.br.tree.residents,self.br.actors)
        self.sim.run(3)
        self.assertGreater(self.br.tree.population,0)
        self.assertEqual(self.b.audit()['rejections'],0)

    def test13_body_tissue_fasting_is_bounded_and_conserved(self):
        fox=self.animal('red_fox');ph=self.br.physical
        for stock in (self.br._short(fox),ph.reserve(fox)):
            q=self.b.energy[stock]
            if q>1e-12:self.b.move(energy=[(stock,'environment:heat',q)])
        body=self.b.mass[ph.live(fox)];tissue=self.b.energy[ph.tissue(fox)]
        previous=self.b.audit()
        provided=self.br._consume_short(fox,.0009,'maintenance')
        self.assertGreater(provided,0)
        self.assertLess(self.b.mass[ph.live(fox)],body)
        self.assertLess(self.b.energy[ph.tissue(fox)],tissue)
        self.assertAlmostEqual(self.b.audit()['mass_total'],previous['mass_total'],places=7)
        self.assertAlmostEqual(self.b.audit()['energy_total'],previous['energy_total'],places=7)
        self.assertEqual(self.b.audit()['rejections'],0)

    def test14_plant_eaters_have_real_trait_limited_intake(self):
        rabbit=self.animal('burrow_rabbit');h=rabbit.habitat
        starting=self.b.mass[self.br.physical.gut(rabbit)]
        self.assertTrue(self.br._feed_stock(rabbit,self.br.tree.acct('plant',h),'plant',dt=1.))
        self.assertGreater(self.b.mass[self.br.physical.gut(rabbit)],starting)
        self.assertGreater(self.br.trophic_metrics['plant_fiber_meals'],0)
        self.assertEqual(self.b.audit()['rejections'],0)

    def test15_intraguild_is_dangerous_not_preferred_forage(self):
        from trophic_roles_146 import PREY_PREFERENCE
        p=PREY_PREFERENCE['ridge_hound']
        self.assertGreater(p['burrow_rabbit'],p['red_fox']*10)
        self.assertGreater(p['meadow_grazer'],p['golden_jackal']*10)
        self.assertGreater(p['red_fox'],0)

    def test16_canid_parent_meal_is_transfer_not_new_food(self):
        mom=self.animal('red_fox','F');dad=self.animal('red_fox','M')
        p=__import__('species_life_02115').PROFILES['red_fox']
        mater=self.br.physical.maternal(mom)
        minimum=p.newborn_mass()*p.litter[0]
        gap=max(0.,minimum-self.b.mass[mater])
        if gap:self.br.physical.convert([(self.br.physical.plant(mom),mater,gap)])
        mom.generation=1;mom.pregnant_until=self.br.day;mom.pregnancy_father=dad.id
        count=self.br._birth(mom)
        self.assertGreater(count,0)
        child=next(x for x in self.br.actors.values() if x.parent==mom.id)
        self.br.positions[child.id]=self.br._pos(mom)
        # A real local carcass funds the mother's gut; the same gut contents
        # can later be physically transferred to dependent offspring.
        self.deposit_carrion(mom.habitat,amount=.05)
        self.br._refresh_quota()
        s=self.br.carrion(mom.habitat)
        best=max([(v,k) for k,v in self.br._cell_quota.items()
                  if k[0]==s and k[1]==mom.habitat],key=lambda x:x[0])[1]
        self.br.positions[mom.id]=(best[1],best[2],best[3]);self.br.positions[child.id]=self.br._pos(mom)
        fed=self.br._feed_stock(mom,s,'parental_meat',dt=2.)
        self.assertTrue(fed)
        before=self.b.audit()
        self.br._care(mom)
        self.assertGreater(self.br.physiology_metrics['provisioned_children']+self.br.trophic_metrics['regurgitated_child_meals'],0)
        self.assertAlmostEqual(self.b.audit()['energy_total'],before['energy_total'],places=7)
        self.assertEqual(self.b.audit()['rejections'],0)

if __name__ == '__main__':unittest.main()
