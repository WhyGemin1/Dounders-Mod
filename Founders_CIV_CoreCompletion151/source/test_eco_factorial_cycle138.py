"""Cycle138 mechanism tests: executable fixtures, no simulated benchmark claims."""
import pickle,unittest
from unittest.mock import patch
from collections import Counter
from src.eco_factorial_cycle138 import UnifiedEcoFactorial138, CELL_COST
from src.integrated_02160 import Unified260
from src.knowledge_family_02142 import KnowledgeFamilyBridge242
from src.habitat_bridge import SPECIES
from src.species_life_02115 import PROFILES, PREY
from experiment_cycle135 import fingerprint

COUNT={s:8 for s in SPECIES}
PARAM=dict(seed=100001,counts=COUNT,five_habitats=True,capacity_scale=0.0,
           family_benefits=True,resource_aware_family=False,grid_size=8,
           colonize_floodplain=True)

def make(**flags):return UnifiedEcoFactorial138(**PARAM,**flags)

def mother_with_child(sim):
    b=sim.bridge
    mothers=[a for a in b.actors.values() if a.alive and a.species=='field_mouse' and a.sex=='F']
    mom=mothers[0]
    father=b.partner(mom)
    mom.pregnant_until=b.day
    mom.pregnancy_father=father.id
    assert b._birth(mom)>=1
    child=next(a for a in b.actors.values() if a.parent==mom.id)
    return mom,child

class Cycle138Tests(unittest.TestCase):
    def test_00_all_off_semantic_parity_through_day30(self):
        original=Unified260(**PARAM);candidate=make()
        self.assertEqual(fingerprint(original),fingerprint(candidate))
        for day in range(1,31):
            original.step();candidate.step()
            self.assertEqual(fingerprint(original),fingerprint(candidate),f'first mismatch day {day}')
        self.assertIs(candidate.host.book,candidate.bridge.book)
        self.assertEqual(original.host.book.audit()['rejections'],0)

    def test_01_flags_not_inferred_and_all_off(self):
        sim=make();self.assertFalse(any(vars(sim.eco_flags).values()))
        with self.assertRaises(TypeError):UnifiedEcoFactorial138(**PARAM,metabolism=1)

    def test_M1_renewal_zero_without_work(self):
        sim=make(metabolism=True);b=sim.host.book;tree=sim.bridge.tree
        # Spend source sunlight by a *legal* Book transfer, not a direct edit.
        transfers=[(tree.acct('sun',h),'house',b.energy[tree.acct('sun',h)])
                   for h in tree.habitats if b.energy[tree.acct('sun',h)]>0]
        if transfers:b.move(energy=transfers)
        sim._extra_metabolism()
        self.assertEqual(sim.eco_flux['new_growth_events'],0)
        self.assertEqual(b.audit()['rejections'],0)

    def test_M2_functional_light_and_water_gating(self):
        wet=make(metabolism=True);dry=make(metabolism=True)
        b=dry.host.book;tree=dry.bridge.tree
        # Drought fixture drains local water into existing cloud reservoir.
        shifts=[(tree.acct('water',h),f'water:tree:{tree.id}:cloud',b.mass[tree.acct('water',h)])
                for h in tree.habitats if b.mass[tree.acct('water',h)]>0]
        if shifts:b.move(material=shifts)
        wet._extra_metabolism();dry._extra_metabolism()
        self.assertGreater(wet.eco_flux['new_growth_mass'],0)
        self.assertEqual(dry.eco_flux['new_growth_mass'],0)
        self.assertGreater(wet.eco_flux['detritus_to_soil'],0)
        self.assertEqual(wet.host.book.audit()['rejections'],0)
        self.assertEqual(dry.host.book.audit()['rejections'],0)

    def test_S1_distant_prey_cannot_be_struck(self):
        sim=make(spatial=True);b=sim.bridge
        hunter=next(a for a in b.actors.values() if a.species=='ridge_hound')
        b.predator_scavenging_enabled=False
        b.sync_positions()
        hunter_cell=(hunter.habitat,0,0);b.positions[hunter.id]=hunter_cell
        for prey in b.actors.values():
            if prey.species in PREY[hunter.species]:
                b.positions[prey.id]=(prey.habitat,7,7)
        before=b.stats['predation']
        self.assertFalse(b._hunt(hunter))
        self.assertEqual(before,b.stats['predation'])
        self.assertGreater(b.eco_metrics['local_hunt_blocked'],0)

    def test_S2_paid_cell_move(self):
        sim=make(spatial=True);b=sim.bridge;a=next(a for a in b.actors.values() if a.species=='meadow_grazer')
        b.day=1;b._refresh_quota()
        old=b._pos(a);before=b.book.energy[b.physical.reserve(a)]
        with patch.object(KnowledgeFamilyBridge242,'_migrate',return_value=False):
            self.assertTrue(b._migrate(a,decision='search'))
        self.assertNotEqual(old,b._pos(a))
        self.assertAlmostEqual(before-b.book.energy[b.physical.reserve(a)],CELL_COST,places=9)
        b.book.audit()

    def test_S3_local_book_quota_not_duplicate_resource(self):
        sim=make(spatial=True);b=sim.bridge;b.day=1;b._refresh_quota()
        for h in b.tree.habitats:
            for source in [b.tree.acct('plant',h),b.carrion(h)]:
                total=sum(q for (s,*_),q in b._cell_quota.items() if s==source)
                self.assertLessEqual(total,b.book.mass[source]+1e-8)
        grazer=next(a for a in b.actors.values() if a.species=='meadow_grazer')
        b.positions[grazer.id]=(grazer.habitat,0,0)
        source=b.physical.plant(grazer)
        before=b.book.mass[source]
        b._feed_stock(grazer,source,'fixture')
        self.assertLessEqual(before-b.book.mass[source],before)
        b.book.audit()

    def test_J1_dependent_caregiver_real_food_and_energy(self):
        sim=make(juvenile=True);b=sim.bridge;mom,child=mother_with_child(sim)
        live=b.physical.live(child);source=b.physical.plant(mom)
        before_mass=b.book.mass[live]
        before_food=b.book.mass[source]
        before_energy=b.book.energy[b.physical.reserve(mom)]
        b._care(mom,'primary')
        self.assertGreater(b.eco_metrics['caregiver_meals'],0)
        self.assertGreater(b.book.mass[live],before_mass)
        self.assertLess(b.book.mass[source],before_food)
        self.assertLess(b.book.energy[b.physical.reserve(mom)],before_energy)
        self.assertEqual(b.book.audit()['rejections'],0)

    def test_J2_juvenile_early_independence_uses_real_digestion(self):
        sim=make(juvenile=True);b=sim.bridge;mom,child=mother_with_child(sim)
        child.age=PROFILES[child.species].independence
        before_mass=b.book.mass[b.physical.live(child)]
        before_chem=b.book.energy[b.physical.chem(child)]
        self.assertTrue(b._feed_stock(child,b.physical.plant(child),'fixture_juvenile'))
        self.assertGreater(b.book.mass[b.physical.live(child)],before_mass)
        self.assertLess(b.book.energy[b.physical.chem(child)],before_chem)
        self.assertGreater(b.fluxes['fixture_juvenile_digestible_energy'],0)
        self.assertEqual(b.book.audit()['rejections'],0)

    def test_J3_no_guaranteed_caregiver_meal(self):
        sim=make(juvenile=True);b=sim.bridge;mom,child=mother_with_child(sim)
        for actor in b.actors.values():
            if actor.parent==mom.id:actor.caregiver_ids.clear()
        b._care(mom,'primary')
        self.assertEqual(b.eco_metrics['caregiver_meals'],0)

    def test_cross_arm_one_day_activations_and_book(self):
        for m in (False,True):
            for s in (False,True):
                for j in (False,True):
                    with self.subTest(M=m,S=s,J=j):
                        sim=make(metabolism=m,spatial=s,juvenile=j)
                        sim.step()
                        self.assertEqual(sim.days,1)
                        self.assertIs(sim.host.book,sim.bridge.tree.book)
                        self.assertEqual(sim.host.book.audit()['rejections'],0)
                        self.assertEqual(sim.eco_flux['new_growth_events']>0,m)
                        self.assertEqual(sim.bridge.eco_metrics['quota_refreshes']>0,s)
                        self.assertEqual(sim.bridge.eco_metrics['caregiver_meals'],0)

    def test_replay_30_to_60_and_full_balance(self):
        sim=make(metabolism=True,spatial=True,juvenile=True)
        for _ in range(30):sim.step()
        frozen=pickle.dumps(sim)
        restored=pickle.loads(frozen)
        self.assertEqual(fingerprint(sim),fingerprint(restored))
        for _ in range(30):sim.step();restored.step()
        self.assertEqual(fingerprint(sim),fingerprint(restored))
        self.assertEqual(sim.eco_flux,restored.eco_flux)
        self.assertEqual(sim.bridge.eco_metrics,restored.bridge.eco_metrics)
        self.assertLess(abs(sim.host.book.audit()['mass_error']),1e-6)
        self.assertLess(abs(sim.host.book.audit()['energy_error']),1e-6)

if __name__=='__main__':unittest.main()
