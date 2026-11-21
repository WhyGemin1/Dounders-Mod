"""Cycle145: source-level gates for funded G1->G2 life cycle and native forage."""
import pickle, unittest
from core_completion_145 import UnifiedCoreCompletion145
from species_life_02115 import PROFILES, MASS_SCALE
from trophic_guilds_cycle138 import ALLOWED_HABITATS

class FivePhase145Tests(unittest.TestCase):
    def setUp(self):
        self.sim=UnifiedCoreCompletion145(seed=100001)
        self.br=self.sim.bridge;self.b=self.sim.host.book
    def species(self,name='burrow_rabbit',sex=None):
        return next(a for a in self.br.actors.values() if a.species==name and (sex is None or a.sex==sex))
    def test01_single_book_world_100_founders_no_time_currency(self):
        self.assertIs(self.b,self.br.book)
        self.assertIs(self.b,self.br.tree.book)
        self.assertEqual(len(self.sim.host.sim.founders.people),100)
        self.assertFalse(hasattr(self.species(),'time_wallet'))
        self.assertEqual(self.b.audit()['rejections'],0)
    def test02_real_mass_growth_after_chronological_maturity(self):
        a=self.species('burrow_rabbit','F');p=PROFILES[a.species]
        self.assertGreaterEqual(a.age,p.maturity)
        original=self.b.mass[self.br.physical.live(a)]
        self.br.physical.convert([(self.br.physical.live(a),self.br.physical.detritus(a),original*.56)])
        starting=self.b.mass[self.br.physical.live(a)]
        meal=self.br._feed_stock(a,self.br.physical.plant(a),'somatic_need',dt=1.)
        self.assertTrue(meal)
        self.br._digest(a,1.)
        self.assertGreater(self.b.mass[self.br.physical.live(a)],starting)
        self.assertGreater(self.br.life_metrics['somatic_growth_from_diet'],0.)
        self.b.audit()
    def test03_nutrition_must_fund_maternal_and_embodied_energy(self):
        a=self.species('burrow_rabbit','F');p=PROFILES[a.species]
        maternal=self.br.physical.maternal(a); before=self.b.mass[maternal]
        self.assertLess(before,p.maternal_cap())
        self.assertTrue(self.br._feed_stock(a,self.br.physical.plant(a),'food',dt=1.))
        self.br._digest(a,1.)
        self.assertGreater(self.b.mass[maternal],before)
        self.assertGreater(self.b.energy[self.br.physical.maternal_energy(a)],0.)
        self.b.audit()
    def test04_birth_cannot_mint_material_and_offspring_inherit(self):
        mom=self.species('burrow_rabbit','F');dad=self.species('burrow_rabbit','M')
        p=PROFILES[mom.species];mom.generation=1
        minimum=p.newborn_mass()*p.litter[0]
        mater=self.br.physical.maternal(mom)
        shortage=max(0.,minimum-self.b.mass[mater])
        if shortage:self.b.move(material=[(self.br.physical.plant(mom),mater,shortage)])
        before_mass=self.b.audit()['mass_total'];before_energy=self.b.audit()['energy_total']
        mom.pregnant_until=self.br.day;mom.pregnancy_father=dad.id
        count=self.br._birth(mom)
        self.assertGreater(count,0)
        children=[a for a in self.br.actors.values() if a.parent==mom.id and a.generation==2]
        self.assertEqual(len(children),count)
        self.assertTrue(all(child.id in self.br.phenotypes for child in children))
        self.assertAlmostEqual(self.b.audit()['mass_total'],before_mass,places=6)
        self.assertAlmostEqual(self.b.audit()['energy_total'],before_energy,places=6)
    def test05_dont_claim_reproduction_when_maternal_empty(self):
        mom=self.species('burrow_rabbit','F')
        maternal=self.br.physical.maternal(mom)
        stock=self.b.mass[maternal]
        if stock:self.br.physical.convert([(maternal,self.br.physical.detritus(mom),stock)])
        self.br.day=120
        self.br._reproduce()
        self.assertIsNone(mom.pregnant_until)
        self.assertGreater(self.br.life_blockers['maternal_mass'],0)
        self.b.audit()
    def test06_native_feeding_respects_fuel_and_gut_capacity(self):
        native=next(a for a in self.br.tree.residents.values() if a.alive)
        oldfuel=self.b.mass[f'fuel:{native.id}']
        if oldfuel<.34:
            self.br.physical.convert([(self.br.tree.acct('plant',native.habitat),f'fuel:{native.id}',.34-oldfuel)])
        gut=self.br.tree._native_gut(native)
        previous=self.b.mass[gut]
        self.assertFalse(self.br.tree._feed(native))
        self.assertEqual(self.b.mass[gut],previous)
        self.b.audit()
    def test07_native_hungry_eats_existing_mass_and_energy(self):
        native=next(a for a in self.br.tree.residents.values() if a.alive)
        habitat=native.habitat;lot=self.br.lots.plant(habitat)
        self.br.lots.balance(habitat)
        mass=self.b.mass[lot.mass_account];en=self.b.energy[lot.energy_account]
        self.assertTrue(self.br.tree._feed(native))
        self.assertLess(self.b.mass[lot.mass_account],mass)
        self.assertLess(self.b.energy[lot.energy_account],en)
        self.assertGreater(self.b.energy[self.br.tree._native_gut_energy(native)],0)
        self.b.audit()
    def test08_no_predation_experiment_still_funds_normal_maintenance(self):
        s=UnifiedCoreCompletion145(seed=100001,predation=False)
        a=next(x for x in s.bridge.actors.values() if x.species=='ridge_hound')
        self.assertFalse(s.bridge._hunt(a))
        self.assertEqual(s.bridge.life_metrics['predation_test_suppressed'],1)
        e=s.host.book.energy[s.bridge._short(a)]
        s.bridge._metabolize(a,dt=.25)
        self.assertLessEqual(s.host.book.energy[s.bridge._short(a)],e)
        s.host.book.audit()
    def test09_maintenance_perturbation_is_physical_not_subsidy(self):
        a=self.species('burrow_rabbit');standard=self.br._maintenance_demand(a)
        self.br.maintenance_factor=.75
        self.assertAlmostEqual(self.br._maintenance_demand(a),standard*.75)
        self.br._metabolize(a,.25)
        self.b.audit()
    def test10_checkpoint_deterministic_book_and_lineages(self):
        self.sim.run(3)
        restored=pickle.loads(pickle.dumps(self.sim))
        self.sim.run(4);restored.run(4)
        self.assertEqual(dict(self.sim.host.book.mass),dict(restored.host.book.mass))
        self.assertEqual(dict(self.sim.host.book.energy),dict(restored.host.book.energy))
        self.assertEqual(self.br.life_blockers,restored.bridge.life_blockers)
        self.assertEqual(self.br.phenotypes,restored.bridge.phenotypes)
        self.assertEqual(self.br.tree.population,restored.bridge.tree.population)
        self.assertEqual(self.b.audit()['rejections'],0)
    def test11_renewable_sun_energy_only_from_book(self):
        old=self.b.audit()['energy_total']
        inflow=self.b.audit()['external_wellspring']
        self.sim.run(3)
        audit=self.b.audit()
        self.assertEqual(audit['rejections'],0)
        # The only legal external inflow is a logged Wellspring transaction.
        self.assertAlmostEqual(audit['energy_total']-old,
                               audit['external_wellspring']-inflow,places=6)
    def test12_synthetic_species_calibration_never_assumed(self):
        self.assertEqual(len(self.br.phenotypes),len(self.br.actors))
        self.assertGreater(self.br._minimum_maternal_mass(PROFILES['burrow_rabbit']),
                           PROFILES['burrow_rabbit'].newborn_mass())
        self.assertTrue(self.sim.report()['core_completion_145']['one_book'])

if __name__=='__main__':unittest.main()
