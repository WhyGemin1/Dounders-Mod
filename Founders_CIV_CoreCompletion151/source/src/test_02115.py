"""Physically funded life-history / species needs / checkpoint regressions."""
import os,tempfile,unittest
from unified_02115 import Unified215
from species_life_02115 import PROFILES, MASS_SCALE

class FixedRandom:
    def random(self):return 0.
    def choice(self,x):return x[0]
    def randint(self,a,b):return a

class LifeHistoryTests(unittest.TestCase):
    def test_single_clock_book_and_distinct_registry(self):
        s=Unified215(seed=9711);s.run(2)
        self.assertIs(s.bridge.book,s.host.sim.book)
        self.assertEqual(s.days,s.host.sim.tick-s.host.bootstrap_tick)
        self.assertEqual(s.host.sim.tick,s.host.sim.ecology.day)
        self.assertEqual(s.bridge.census()['combined_unique'],s.bridge.census()['bridge_total']+s.bridge.tree.population)
        self.assertEqual(s.host.book.audit()['rejections'],0)

    def test_profile_stage_gestation_litter_and_pilot_scale(self):
        p=PROFILES['field_mouse']
        self.assertEqual((p.independence,p.maturity,p.senescence,p.max_age),(12,36,130,225))
        self.assertEqual((p.gestation,p.litter,p.breeding),(12,(2,3),(20,325)))
        self.assertEqual((p.stage(11),p.stage(12),p.stage(36),p.stage(130)),
                         ('dependent','juvenile','adult','elder'))
        self.assertAlmostEqual(p.newborn_mass(),.055*MASS_SCALE)
        self.assertEqual(PROFILES['ridge_hound'].maturity,180)

    def test_birth_transfers_maternal_mass_not_plant(self):
        s=Unified215(seed=9711)
        b=s.bridge
        mother=next(a for a in b.actors.values() if a.species=='field_mouse' and a.sex=='F' and a.stage=='adult')
        father=next(a for a in b.actors.values() if a.species=='field_mouse' and a.sex=='M')
        before_mom=s.host.book.mass[f'maternal:{mother.id}']
        before_plant=s.host.book.mass[b.tree.acct('plant',mother.habitat)]
        before_total=s.host.book.audit()['mass_total']
        mother.pregnancy_father=father.id;mother.pregnant_until=1;b.day=1
        b.rng=FixedRandom()
        n=b._birth(mother)
        self.assertGreaterEqual(n,1)
        self.assertEqual(b.stats['birth'],n)
        self.assertAlmostEqual(s.host.book.mass[f'maternal:{mother.id}'],before_mom-n*PROFILES[mother.species].newborn_mass())
        self.assertAlmostEqual(s.host.book.mass[b.tree.acct('plant',mother.habitat)],before_plant)
        self.assertAlmostEqual(s.host.book.audit()['mass_total'],before_total)
        children=[a for a in b.actors.values() if a.parent==mother.id]
        self.assertEqual(len(children),n)
        self.assertTrue(all(a.habitat==mother.habitat and a.sex in ('F','M') and a.stage=='dependent' for a in children))
        self.assertTrue(all(a.caregiver_ids=={mother.id} for a in children))
        b._check_registry()

    def test_failed_birth_without_maternal_stock(self):
        s=Unified215(seed=9711);b=s.bridge
        mother=next(a for a in b.actors.values() if a.species=='field_mouse' and a.sex=='F' and a.stage=='adult')
        father=next(a for a in b.actors.values() if a.species=='field_mouse' and a.sex=='M')
        q=s.host.book.mass[f'maternal:{mother.id}']
        if q:b.physical.convert([(f'maternal:{mother.id}',b.tree.acct('detritus',mother.habitat),q)])
        mother.pregnant_until=1;mother.pregnancy_father=father.id;b.day=1
        self.assertEqual(b._birth(mother),0)
        self.assertEqual(b.stats['failed_birth'],1)
        self.assertFalse(any(e['event']=='birth' for e in b.events))
        self.assertEqual(s.host.book.audit()['rejections'],0)

    def test_conception_requires_adults_local_mate_and_due_date(self):
        s=Unified215(seed=9711);b=s.bridge
        female=next(a for a in b.actors.values() if a.species=='field_mouse' and a.sex=='F')
        male=next(a for a in b.actors.values() if a.species=='field_mouse' and a.sex=='M')
        female.age=45;male.age=45;female.condition=1.;male.condition=1.
        female.habitat=male.habitat='grassland'
        # This is a test fixture funded with an actual plant debit, not mutation.
        needed=PROFILES['field_mouse'].birth_cost*MASS_SCALE-s.host.book.mass[f'maternal:{female.id}']
        if needed>0:b.physical.convert([(b.tree.acct('plant','grassland'),f'maternal:{female.id}',needed)])
        b.day=60;b.rng=FixedRandom()
        b._reproduce()
        self.assertEqual(female.pregnant_until,72)
        self.assertEqual(female.pregnancy_father,male.id)
        b.day=71;b._reproduce();self.assertEqual(b.stats['birth'],0)
        b.day=72;b._reproduce();self.assertGreater(b.stats['birth'],0)
        self.assertEqual(s.host.book.audit()['rejections'],0)

    def test_predation_locality_cover_and_physical_carrion(self):
        s=Unified215(seed=9711);b=s.bridge
        predator=next(a for a in b.actors.values() if a.species=='ridge_hound')
        self.assertFalse(b._hunt(predator)) # no matching prey in ridge on initialization
        victim=next(a for a in b.actors.values() if a.species=='field_mouse')
        predator.habitat=victim.habitat
        b.rng=FixedRandom()
        before=s.host.book.mass[f'live:{victim.id}']
        maternal=s.host.book.mass[f'maternal:{victim.id}']
        self.assertTrue(b._hunt(predator))
        self.assertFalse(victim.alive)
        self.assertAlmostEqual(s.host.book.mass[b.carrion(victim.habitat)],before*.7+maternal)
        self.assertEqual(s.host.book.mass[f'live:{victim.id}'],0.)
        self.assertEqual(s.host.book.audit()['rejections'],0)
        b._check_registry()

    def test_local_needs_hide_without_guaranteed_safety(self):
        s=Unified215(seed=9711);b=s.bridge
        prey=next(a for a in b.actors.values() if a.species=='field_mouse' and a.stage!='dependent')
        predator=next(a for a in b.actors.values() if a.species=='ridge_hound')
        predator.habitat=prey.habitat
        # Physically funded food-security buffer; no direct reserve mutation.
        s.host.book.move(energy=[('house',f'animal:{prey.id}',.20)])
        b.rng=FixedRandom()
        action,hunger,threat=b.evaluate_needs(prey)
        self.assertTrue(threat)
        self.assertEqual(action,'hide')
        self.assertFalse(b._migrate(prey,action))
        self.assertTrue(prey.hidden)
        self.assertGreater(b.stats['need_transition'],0)
        # Hidden prey can still be found in a worst-case synthetic trial.
        self.assertTrue(b._hunt(predator))
        self.assertFalse(prey.alive)
        self.assertEqual(s.host.book.audit()['rejections'],0)

    def test_parental_care_is_optional_and_book_funded(self):
        s=Unified215(seed=9711);b=s.bridge
        mother=next(a for a in b.actors.values() if a.species=='field_mouse' and a.sex=='F' and a.stage=='adult')
        father=next(a for a in b.actors.values() if a.species=='field_mouse' and a.sex=='M')
        mother.pregnancy_father=father.id;mother.pregnant_until=1;b.day=1;b.rng=FixedRandom()
        n=b._birth(mother)
        self.assertGreater(n,0)
        child=next(a for a in b.actors.values() if a.parent==mother.id)
        s.host.book.move(energy=[('house',f'animal:{mother.id}',.20)])
        action,_,_=b.evaluate_needs(mother)
        self.assertEqual(action,'care')
        old_child=s.host.book.energy[f'animal:{child.id}']
        old_parent=s.host.book.energy[f'animal:{mother.id}']
        b._care(mother)
        self.assertGreater(s.host.book.energy[f'animal:{child.id}'],old_child)
        self.assertLess(s.host.book.energy[f'animal:{mother.id}'],old_parent)
        self.assertEqual(s.host.book.audit()['rejections'],0)

    def test_secondary_care_is_finite_and_book_funded(self):
        s=Unified215(seed=9711);b=s.bridge
        mother=next(a for a in b.actors.values() if a.species=='field_mouse' and a.sex=='F' and a.stage=='adult')
        father=next(a for a in b.actors.values() if a.species=='field_mouse' and a.sex=='M')
        mother.pregnancy_father=father.id;mother.pregnant_until=1;b.day=1;b.rng=FixedRandom()
        b._birth(mother)
        child=next(a for a in b.actors.values() if a.parent==mother.id)
        s.host.book.move(energy=[('house',f'animal:{mother.id}',.03)])
        before=s.host.book.energy[f'animal:{mother.id}']+sum(s.host.book.energy[f'animal:{x.id}'] for x in b.actors.values() if x.parent==mother.id)
        b._care(mother,episode='secondary')
        after=s.host.book.energy[f'animal:{mother.id}']+sum(s.host.book.energy[f'animal:{x.id}'] for x in b.actors.values() if x.parent==mother.id)
        self.assertAlmostEqual(before,after)
        self.assertTrue(any(e['event']=='parental_care' and e.get('episode')=='secondary' for e in b.events))
        self.assertEqual(s.host.book.audit()['rejections'],0)

    def test_caregiver_cannot_mint_energy_when_depleted(self):
        s=Unified215(seed=9711);b=s.bridge
        mother=next(a for a in b.actors.values() if a.species=='field_mouse' and a.sex=='F' and a.stage=='adult')
        father=next(a for a in b.actors.values() if a.species=='field_mouse' and a.sex=='M')
        mother.pregnancy_father=father.id;mother.pregnant_until=1;b.day=1;b.rng=FixedRandom()
        b._birth(mother)
        e=s.host.book.energy[f'animal:{mother.id}']
        if e>s.bridge.TRAVEL_COST:s.host.book.move(energy=[(f'animal:{mother.id}','environment:heat',e)])
        before=b.stats['parental_care'];b._care(mother,episode='secondary')
        self.assertEqual(before,b.stats['parental_care'])
        self.assertEqual(s.host.book.audit()['rejections'],0)

    def test_checkpoint_replay(self):
        s=Unified215(seed=9712)
        s.run(10)
        with tempfile.TemporaryDirectory() as tmp:
            path=os.path.join(tmp,'checkpoint.pkl')
            s.save(path)
            clone=Unified215.load(path)
            self.assertEqual(s.run(20),clone.run(20))

    def test_actual_collapse_transfers_maternal_and_body_stocks(self):
        s=Unified215(seed=9714);b=s.bridge
        b.tree.collapse('test')
        b.step(1)
        self.assertTrue(all(not a.alive for a in b.actors.values()))
        for a in b.actors.values():
            for tag in ('live','maternal','gut'):
                self.assertAlmostEqual(s.host.book.mass[f'{tag}:{a.id}'],0.)
        self.assertEqual(s.host.book.audit()['rejections'],0)

if __name__=='__main__':unittest.main()
