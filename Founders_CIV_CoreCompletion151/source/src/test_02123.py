"""Fast physical, behavioral and replay tests for two-agent integration."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from unified_02122 import Unified222
from unified_02123 import Unified223
from species_life_02115 import PROFILES, MASS_SCALE
from stateful_mouse_needs_02123 import mouse_hunger_transition

class CrossAgentIntegrationTests(unittest.TestCase):
    def test_hysteresis_thresholds(self):
        self.assertTrue(mouse_hunger_transition(.018,False))
        self.assertTrue(mouse_hunger_transition(.035,True))
        self.assertFalse(mouse_hunger_transition(.06,True))
        self.assertFalse(mouse_hunger_transition(.035,False))

    def test_default_identical_to_latest_agent(self):
        a=Unified222(seed=9711,digestion=True,predator_scavenging=True,mate_search=False)
        b=Unified223(seed=9711,digestion=True,predator_scavenging=True,mate_search=False)
        ra=a.run(3);rb=b.run(3)
        for key in ('species','bridge_events','tree_state','tree_population','ledger'):
            self.assertEqual(ra[key],rb[key],key)

    def test_source_book_one_clock(self):
        s=Unified223(seed=9711,digestion=True,predator_scavenging=True,
                     mate_search=True,mouse_hysteresis=True)
        self.assertIs(s.bridge.book,s.host.book)
        s.run(3)
        self.assertEqual(s.days,s.bridge.day)
        self.assertEqual(s.host.book.audit()['rejections'],0)

    def test_hound_forced_adjacent_cue_is_paid(self):
        s=Unified223(seed=9711,digestion=True,mate_search=True)
        b=s.bridge; hounds=[a for a in b.actors.values() if a.species=='ridge_hound']
        mover=next(x for x in hounds if x.sex=='F' and b.book.mass[b.physical.maternal(x)]>=PROFILES['ridge_hound'].birth_cost*.012)
        partner=next(x for x in hounds if x.sex != mover.sex and x.stage=='adult')
        mover.age=PROFILES['ridge_hound'].maturity+3
        partner.age=PROFILES['ridge_hound'].maturity+4
        mover.condition=partner.condition=1.
        b.day=60
        maternal=b.physical.maternal(mover)
        required=PROFILES['ridge_hound'].birth_cost*MASS_SCALE
        shortfall=max(0.,required-b.book.mass[maternal]+.004)
        if shortfall:
            b.physical.convert([(b.physical.plant(mover),maternal,shortfall)])
        adjacent=tuple(b.tree.habitats[mover.habitat].neighbors)
        self.assertTrue(adjacent)
        partner.habitat=adjacent[0]  # controlled spatial fixture; does not create resources
        before_mass=sum(b.book.mass.values())
        before_energy=sum(b.book.energy.values())
        before=b.book.energy[b.physical.reserve(mover)]
        cost=b.TRAVEL_COST*1.35
        with patch.object(b.rng,'random',return_value=0.):
            self.assertTrue(b._migrate(mover,'search'))
        self.assertEqual(mover.habitat,partner.habitat)
        self.assertAlmostEqual(before-b.book.energy[b.physical.reserve(mover)],cost,places=9)
        self.assertAlmostEqual(sum(b.book.mass.values()),before_mass,places=8)
        self.assertAlmostEqual(sum(b.book.energy.values()),before_energy,places=8)
        self.assertEqual(b.fluxes['mate_search_moves'],1)
        self.assertEqual(b.book.audit()['rejections'],0)

    def test_mate_cue_rejected_for_juvenile(self):
        s=Unified223(seed=9711,digestion=True,mate_search=True)
        b=s.bridge; hounds=[a for a in b.actors.values() if a.species=='ridge_hound']
        a=hounds[0];other=next(x for x in hounds if x.sex!=a.sex)
        a.age=2;b.day=60
        other.age=PROFILES['ridge_hound'].maturity+1
        other.habitat=tuple(b.tree.habitats[a.habitat].neighbors)[0]
        with patch.object(b.rng,'random',return_value=0.):
            self.assertEqual(b.fluxes['mate_search_moves'],0)
            b._migrate(a,'search')
        self.assertEqual(b.fluxes['mate_search_moves'],0)

    def test_mate_search_requires_actual_conception_stock(self):
        s=Unified223(seed=9711,digestion=True,mate_search=True)
        b=s.bridge
        mom=next(x for x in b.actors.values() if x.species=='ridge_hound' and x.sex=='F' and x.stage=='adult')
        male=next(x for x in b.actors.values() if x.species=='ridge_hound' and x.sex=='M' and x.stage=='adult')
        male.habitat=tuple(b.tree.habitats[mom.habitat].neighbors)[0]
        b.day=60
        self.assertLess(b.book.mass[b.physical.maternal(mom)],PROFILES['ridge_hound'].birth_cost*MASS_SCALE)
        b._migrate(mom,'search')
        self.assertGreater(b.integration_fluxes['mate_gate_maternal_shortfall'],0)
        self.assertEqual(b.fluxes['mate_search_moves'],0)
        self.assertEqual(b.book.audit()['rejections'],0)

    def test_funded_mate_search_can_reach_conception_and_birth_fixture(self):
        s=Unified223(seed=9711,digestion=True,mate_search=True)
        b=s.bridge
        mom=next(x for x in b.actors.values() if x.species=='ridge_hound' and x.sex=='F' and x.stage=='adult')
        male=next(x for x in b.actors.values() if x.species=='ridge_hound' and x.sex=='M' and x.stage=='adult')
        b.day=60
        required=PROFILES['ridge_hound'].birth_cost*MASS_SCALE
        b.physical.convert([(b.physical.plant(mom),b.physical.maternal(mom),required)])
        male.habitat=tuple(b.tree.habitats[mom.habitat].neighbors)[0]
        before_mass=sum(b.book.mass.values())
        before_energy=sum(b.book.energy.values())
        with patch.object(b.rng,'random',return_value=0.):
            self.assertTrue(b._migrate(mom,'search'))
            b._reproduce()
        self.assertIsNotNone(mom.pregnant_until)
        b.day=mom.pregnant_until
        self.assertGreater(b._birth(mom),0)
        self.assertGreater(b.stats['birth'],0)
        self.assertAlmostEqual(sum(b.book.mass.values()),before_mass,places=8)
        self.assertAlmostEqual(sum(b.book.energy.values()),before_energy,places=8)
        self.assertEqual(b.book.audit()['rejections'],0)

    def test_dispersion_charges_hound_reserves(self):
        a=Unified223(seed=9711,digestion=True,mate_search=True,
                     initial_hound_dispersion=False)
        b=Unified223(seed=9711,digestion=True,mate_search=True,
                     initial_hound_dispersion=True)
        moved=b.bridge.integration_fluxes['dispersion_moves']
        self.assertEqual(moved,2)
        self.assertAlmostEqual(sum(a.host.book.energy.values()),sum(b.host.book.energy.values()),places=8)
        self.assertEqual(b.host.book.audit()['rejections'],0)

    def test_mouse_satiation_prevents_unneeded_book_debit(self):
        s=Unified223(seed=9711,digestion=True,mouse_hysteresis=True)
        b=s.bridge
        mouse=next(a for a in b.actors.values() if a.species=='field_mouse')
        account=b.physical.reserve(mouse)
        reserve=b.book.energy[account]
        # Entirely existing environment chemicals; fixture does not mint energy.
        chem=b.physical.chem(mouse)
        b.book.move(energy=[(chem,account,.06-reserve)])
        before=b.book.energy[chem]
        b.mouse_hungry[mouse.id]=False
        self.assertFalse(b._feed_herbivore(mouse))
        self.assertAlmostEqual(b.book.energy[chem],before)
        self.assertEqual(b.integration_fluxes['mouse_satiated_skips'],1)
        b.book.move(energy=[(account,'environment:heat',.047)])
        self.assertTrue(mouse_hunger_transition(b.book.energy[account],False))
        self.assertTrue(b._feed_herbivore(mouse))
        self.assertGreater(b.integration_fluxes['mouse_funded_meals'],0)
        self.assertEqual(b.book.audit()['rejections'],0)

    def test_checkpoint_replay_crossagent_state(self):
        s=Unified223(seed=9712,digestion=True,predator_scavenging=True,
                     mate_search=True,mouse_hysteresis=True,initial_hound_dispersion=True)
        s.run(3)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'restart.pkl'
            s.save(path)
            other=Unified223.load(path)
            self.assertEqual(s.run(3),other.run(3))
            self.assertEqual(s.bridge.integration_fluxes,other.bridge.integration_fluxes)

    def test_scavenging_flag_not_accidentally_enabled_by_mate_search(self):
        off=Unified223(seed=9711,digestion=True,mate_search=True,predator_scavenging=False)
        on=Unified223(seed=9711,digestion=True,mate_search=True,predator_scavenging=True)
        for s in (off,on):
            hounds=[a for a in s.bridge.actors.values() if a.species=='ridge_hound']
            s.bridge._death(hounds[1],'controlled_carcass')
            self.assertGreater(s.bridge.book.mass[s.bridge.carrion(hounds[0].habitat)],0)
        h_off=next(a for a in off.bridge.actors.values() if a.species=='ridge_hound' and a.alive)
        h_on=next(a for a in on.bridge.actors.values() if a.species=='ridge_hound' and a.alive)
        self.assertFalse(off.bridge._hunt(h_off))
        self.assertTrue(on.bridge._hunt(h_on))
        self.assertEqual(off.bridge.fluxes['predator_scavenge_meals'],0)
        self.assertEqual(on.bridge.fluxes['predator_scavenge_meals'],1)
        self.assertEqual(off.host.book.audit()['rejections'],0)
        self.assertEqual(on.host.book.audit()['rejections'],0)

    def test_native_lifecycle_remains_unmodified(self):
        s=Unified223(seed=9711,digestion=True,mouse_hysteresis=True,mate_search=True)
        s.bridge.tree.state='archived'
        s.bridge.step(1)
        self.assertFalse(any(a.alive for a in s.bridge.actors.values()))
        self.assertEqual(s.bridge.book.audit()['rejections'],0)

if __name__=='__main__':unittest.main()
