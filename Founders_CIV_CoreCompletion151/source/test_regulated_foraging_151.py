"""Contract tests for Cycle151's single physiological foraging decision."""
import pickle
import unittest
from unified_foraging_151 import UnifiedRegulatedForaging151, TARGET_MAINTENANCE_DAYS
from integration_cleanup_150 import UnifiedCleanup150
from trophic_roles_146 import CARNIVORE_ROLES
from trophic_guilds_cycle138 import _temporary_diet_registry


class RegulatedForaging151Tests(unittest.TestCase):
    def setUp(self):
        self.sim=UnifiedRegulatedForaging151(seed=100001)
        self.br=self.sim.bridge
        self.b=self.sim.host.book
        self.ctx=_temporary_diet_registry();self.ctx.__enter__()

    def tearDown(self):
        self.ctx.__exit__(None,None,None)

    def animal(self,sp):
        return next(a for a in self.br.actors.values() if a.alive and a.species==sp)

    def make_hungry(self,a):
        # Explicitly remove existing food energy via a balanced physical transfer.
        # No direct account edits, and no animal is spawned or artificially saved.
        b=self.b;br=self.br
        for source in (br.physical.reserve(a),br._short(a)):
            existing=b.energy[source]
            want=min(existing,max(0.,existing-br._maintenance_demand(a)*.65))
            if want>1e-12:
                b.move(energy=[(source,'environment:heat',want)])
        return br._foraging_state151(a)

    def test_01_shared_book_founders_and_species(self):
        self.assertIs(self.b,self.br.book)
        self.assertIs(self.b,self.br.tree.book)
        self.assertEqual(len(self.sim.host.sim.founders.people),100)
        self.assertEqual(len({a.species for a in self.br.actors.values()}),13)
        self.assertEqual(self.b.audit()['rejections'],0)

    def test_02_well_fed_hound_does_not_initiate_hunt(self):
        a=self.animal('ridge_hound')
        assessment=self.br._foraging_state151(a)
        self.assertGreater(assessment.available_days,TARGET_MAINTENANCE_DAYS['ridge_hound'])
        self.assertFalse(assessment.nutritional_need)
        act,_,danger=self.br._choose(a)
        self.assertFalse(danger)
        self.assertEqual(act,'rest')
        initial=self.b.audit()['energy_total']
        self.assertFalse(self.br._hunt(a))
        self.assertGreater(self.br.regulation151_metrics['unnecessary_strikes_prevented'],0)
        self.assertAlmostEqual(self.b.audit()['energy_total'],initial,places=6)

    def test_03_hungry_hound_is_not_permanently_blocked(self):
        a=self.animal('ridge_hound')
        assessed=self.make_hungry(a)
        self.assertTrue(assessed.nutritional_need)
        self.assertTrue(assessed.has_gut_room)
        act,_,danger=self.br._choose(a)
        self.assertFalse(danger)
        self.assertEqual(act,'feed')
        self.assertEqual(self.b.audit()['rejections'],0)

    def test_04_species_specific_satiation_contracts(self):
        self.assertEqual(set(TARGET_MAINTENANCE_DAYS),set(CARNIVORE_ROLES))
        for sp in CARNIVORE_ROLES:
            a=self.animal(sp)
            obs=self.br._foraging_state151(a)
            self.assertGreater(obs.stomach_capacity,obs.gut_mass)
            self.assertGreater(obs.daily_maintenance,0)
            self.assertGreaterEqual(obs.available_days,0)

    def test_05_gut_capacity_defer_even_if_reserves_low(self):
        a=self.animal('red_fox')
        self.make_hungry(a)
        # Using Book ingestion, place previously existing food mass and
        # embodied energy into the real gut. No synthetic raw account changes.
        lot=self.br.lots.plant(a.habitat)
        self.br.lots.balance(a.habitat)
        cap=self.br._foraging_state151(a).stomach_capacity
        q=min(cap*.76,self.br.lots.available_mass(lot))
        self.assertGreater(q,cap*.70)
        self.b.ingest(material=[(lot.mass_account,self.br.physical.gut(a),q)],
                      energy=[(lot.energy_account,self.br._gut_energy(a),q*lot.nominal_density)])
        st=self.br._state(a);st.gut_energy_weight+=q*lot.nominal_density
        st.gut_quality_weight+=q*lot.nominal_density*.55
        self.assertFalse(self.br._foraging_state151(a).has_gut_room)
        self.assertEqual(self.br._choose(a)[0],'rest')
        self.assertFalse(self.br._hunt(a))
        self.assertEqual(self.b.audit()['rejections'],0)

    def test_06_plant_eaters_keep_inherited_decisions(self):
        a=self.animal('burrow_rabbit')
        from integration_cleanup_150 import CleanBridge150
        self.assertEqual(self.br._choose(a),CleanBridge150._choose(self.br,a))

    def test_07_feature_off_exact_core150_fingerprint(self):
        off=UnifiedRegulatedForaging151(seed=100001,regulated_foraging=False)
        ref=UnifiedCleanup150(seed=100001)
        for _ in range(3):
            off.step();ref.step()
        self.assertEqual(dict(off.host.book.mass),dict(ref.host.book.mass))
        self.assertEqual(dict(off.host.book.energy),dict(ref.host.book.energy))
        self.assertEqual(off.bridge.positions,ref.bridge.positions)
        self.assertEqual(off.bridge.events,ref.bridge.events)
        self.assertEqual(off.report()['species'],ref.report()['species'])

    def test_08_checkpoint_replay_matches_uninterrupted(self):
        self.sim.run(2)
        clone=pickle.loads(pickle.dumps(self.sim,pickle.HIGHEST_PROTOCOL))
        self.sim.run(2);clone.run(2)
        self.assertEqual(dict(self.sim.host.book.mass),dict(clone.host.book.mass))
        self.assertEqual(dict(self.sim.host.book.energy),dict(clone.host.book.energy))
        self.assertEqual(self.sim.bridge.positions,clone.bridge.positions)
        self.assertEqual(dict(self.sim.bridge.regulation151_metrics),dict(clone.bridge.regulation151_metrics))

    def test_09_physiological_collapse_requires_actual_depletion(self):
        a=self.animal('ridge_hound')
        st=self.br._state(a)
        st.starvation_debt=1.10
        self.assertFalse(self.br._fatal_condition(a,st))
        a.condition=.05
        self.assertTrue(self.br._fatal_condition(a,st))
        old=UnifiedRegulatedForaging151(seed=100001,regulated_foraging=False)
        h=next(x for x in old.bridge.actors.values() if x.species=='ridge_hound')
        st_old=old.bridge._state(h)
        st_old.starvation_debt=1.10
        self.assertTrue(old.bridge._fatal_condition(h,st_old))

    def test_10_emergency_fuel_can_pay_real_strike_without_minting(self):
        a=self.animal('ridge_hound')
        candidate=next(p for p in self.br.actors.values() if p.alive and
            p.species in ('field_mouse','meadow_grazer','burrow_rabbit','field_vole'))
        candidate.habitat=a.habitat
        self.br.positions[candidate.id]=self.br._pos(a)
        for source in (self.br.physical.reserve(a),self.br._short(a)):
            q=self.b.energy[source]
            if q>1e-12:self.b.move(energy=[(source,'environment:heat',q)])
        tissue_before=self.b.energy[self.br.physical.tissue(a)]
        body_before=self.b.mass[self.br.physical.live(a)]
        initial_energy=self.b.audit()['energy_total']
        self.assertTrue(self.br._work(a,'strike',effort=1.55))
        self.assertGreater(self.br.regulation151_metrics['emergency_strike_fuel'],0.)
        self.assertLess(self.b.mass[self.br.physical.live(a)],body_before)
        self.assertLess(self.b.energy[self.br.physical.tissue(a)],tissue_before)
        self.assertAlmostEqual(self.b.audit()['energy_total'],initial_energy,places=5)
        self.assertEqual(self.b.audit()['rejections'],0)

    def test_11_hound_pursues_safer_prey_before_competitor(self):
        self.br.intraguild_risk151=True  # experimental ablation
        h=self.animal('ridge_hound')
        competitor=self.animal('golden_jackal')
        ordinary=self.animal('burrow_rabbit')
        here=(h.habitat,0,0)
        self.br.positions[h.id]=here
        competitor.habitat=h.habitat;ordinary.habitat=h.habitat
        self.br.positions[competitor.id]=(h.habitat,0,1)
        self.br.positions[ordinary.id]=(h.habitat,0,2)
        # Clear other accessible ordinary prey from this local 2-cell test.
        for other in self.br.actors.values():
            if other.id in (h.id,competitor.id,ordinary.id):continue
            if other.species in ('field_mouse','meadow_grazer','burrow_rabbit','field_vole') and other.habitat==h.habitat:
                self.br.positions[other.id]=(h.habitat,7,7)
        basal=self.br._maintenance_demand(h)
        for source,keep in ((self.br.physical.reserve(h),basal*5.),(self.br._short(h),basal*1.0)):
            excess=max(0.,self.b.energy[source]-keep)
            if excess>1e-12:self.b.move(energy=[(source,'environment:heat',excess)])
        self.assertTrue(self.br._foraging_state151(h).nutritional_need)
        self.assertGreater(self.br._foraging_state151(h).available_days,1.5)
        result=self.br._hunt(h)
        self.assertFalse(result)
        self.assertTrue(competitor.alive)
        self.assertGreater(self.br.regulation151_metrics['safer_prey_pursuit_instead_of_intraguild'],0)
        self.assertEqual(self.br._pos(h),(h.habitat,0,1))
        self.assertEqual(self.b.audit()['rejections'],0)

if __name__=='__main__':unittest.main()
