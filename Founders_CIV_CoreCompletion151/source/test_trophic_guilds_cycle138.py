"""Cycle138-G physical, ecological and non-regression tests. No success claims are inferred."""
import pickle, unittest
from unittest.mock import patch
from habitat_bridge import SPECIES, PREY
from species_life_02115 import PROFILES
from integrated_02160 import Unified260
from trophic_guilds_cycle138 import (
    UnifiedTrophicGuild138, GUILD_FOUNDERS, MIN_QUEEN_MASS,
    _temporary_diet_registry)
from experiment_cycle135 import fingerprint

ARGS=dict(seed=100001,counts={s:8 for s in SPECIES},five_habitats=True,
          capacity_scale=0.,family_benefits=True,resource_aware_family=False,
          grid_size=8,colonize_floodplain=True,governance='collective')
def make(**kw):return UnifiedTrophicGuild138(**ARGS,**kw)

class TrophicTests(unittest.TestCase):
    def test_01_disabled_matches_original_cycle135(self):
        original=Unified260(**ARGS);disabled=make(expanded_food_web=False)
        self.assertEqual(fingerprint(original),fingerprint(disabled))
        for day in range(1,11):
            original.step();disabled.step()
            self.assertEqual(fingerprint(original),fingerprint(disabled),day)

    def test_02_funded_founders_and_single_book(self):
        s=make(expanded_food_web=True);b=s.bridge
        self.assertEqual(sum(GUILD_FOUNDERS.values()),28)
        self.assertEqual(len(b.actors),68)
        self.assertEqual(len(s.host.sim.founders.people),100)
        self.assertIs(s.host.book,b.book)
        self.assertIs(b.book,b.tree.book)
        self.assertEqual(s.host.book.audit()['rejections'],0)
        self.assertGreater(sum(s.host.book.mass[b.physical.live(a)] for a in b.actors.values() if a.species in GUILD_FOUNDERS),0)

    def test_03_diet_patching_scope_and_restoration(self):
        self.assertEqual(PREY,{'ridge_hound':('field_mouse','meadow_grazer')})
        with _temporary_diet_registry():
            self.assertIn('burrow_rabbit',PREY['ridge_hound'])
            self.assertIn('red_fox',PREY)
        self.assertEqual(PREY,{'ridge_hound':('field_mouse','meadow_grazer')})
        with self.assertRaises(RuntimeError):
            with _temporary_diet_registry():raise RuntimeError('testing rollback')
        self.assertEqual(PREY,{'ridge_hound':('field_mouse','meadow_grazer')})

    def test_04_fast_preys_and_slow_megafauna(self):
        self.assertEqual(PROFILES['burrow_rabbit'].gestation,30)
        self.assertLess(PROFILES['field_vole'].maturity,PROFILES['red_fox'].maturity)
        self.assertGreater(PROFILES['woolly_mammoth'].maturity,1080)
        self.assertEqual(PROFILES['ant_colony'].independence,0)

    def test_05_ant_worker_brood_book_funded(self):
        s=make(expanded_food_web=True);b=s.bridge
        ant=next(x for x in b.actors.values() if x.species=='ant_colony')
        book=b.book;body=b.physical.live(ant);det=b.tree.acct('detritus',ant.habitat);soil=b.tree.acct('soil',ant.habitat)
        before=(book.mass[body],book.mass[det],book.mass[soil]);b.day=6
        b._ant_brood(ant)
        self.assertAlmostEqual(book.mass[body]-before[0],.0007)
        self.assertAlmostEqual(book.mass[det]-before[1],-.0020)
        self.assertAlmostEqual(book.mass[soil]-before[2],.0013)
        self.assertEqual(b.guild_metrics['brood_episodes'],1)
        self.assertEqual(book.audit()['rejections'],0)

    def test_06_shrew_consumes_workers_not_queen(self):
        s=make(expanded_food_web=True,spatial=True);b=s.bridge
        ant=next(x for x in b.actors.values() if x.species=='ant_colony')
        shrew=next(x for x in b.actors.values() if x.species=='insectivore_shrew' and x.habitat==ant.habitat)
        b.positions[shrew.id]=b._pos(ant)
        pre=b.book.mass[b.physical.live(ant)]
        self.assertTrue(b._ant_worker_take(shrew))
        self.assertTrue(ant.alive)
        self.assertLess(b.book.mass[b.physical.live(ant)],pre)
        self.assertGreaterEqual(b.book.mass[b.physical.live(ant)],MIN_QUEEN_MASS)
        self.assertEqual(b.book.audit()['rejections'],0)

    def test_07_megafauna_impact_real_material_transform(self):
        s=make(expanded_food_web=True);b=s.bridge
        elephant=next(x for x in b.actors.values() if x.species=='forest_elephant')
        book=b.book;h=elephant.habitat
        plant=b.tree.acct('plant',h);soil=b.tree.acct('soil',h)
        oldplant=book.mass[plant];oldsoil=book.mass[soil];tolls=book.toll_count
        b.day=5;b._megaherbivore_turnover(elephant)
        self.assertLess(book.mass[plant],oldplant)
        self.assertGreater(book.mass[soil],oldsoil)
        self.assertGreater(book.toll_count,tolls)
        self.assertEqual(book.audit()['rejections'],0)

    def test_08_fox_can_eat_rabbit_and_hound_fox(self):
        s=make(expanded_food_web=True,spatial=False);b=s.bridge
        fox=next(x for x in b.actors.values() if x.species=='red_fox')
        rabbit=next(x for x in b.actors.values() if x.species=='burrow_rabbit' and x.habitat==fox.habitat)
        with _temporary_diet_registry(),patch.object(b.rng,'random',return_value=0.),patch.object(b.rng,'choice',return_value=rabbit):
            self.assertTrue(b._hunt(fox))
        self.assertFalse(rabbit.alive)
        self.assertGreater(b.stats['predation'],0)
        self.assertEqual(b.book.audit()['rejections'],0)

    def test_09_canid_carrion_provisions_dependents(self):
        s=make(expanded_food_web=True,juvenile=True);b=s.bridge
        fox=next(x for x in b.actors.values() if x.species=='red_fox' and x.sex=='F')
        father=next(x for x in b.actors.values() if x.species=='red_fox' and x.sex=='M')
        fox.pregnant_until=b.day;fox.pregnancy_father=father.id
        self.assertGreaterEqual(b._birth(fox),1)
        child=next(x for x in b.actors.values() if x.parent==fox.id)
        site=b.carrion(fox.habitat)
        source=b.tree.acct('plant',fox.habitat)
        b.physical.convert([(source,site,.04)])
        b.day=2;b._care(fox,episode='primary')
        self.assertGreaterEqual(b.guild_metrics['canid_dependent_provisions'],1)
        self.assertGreater(b.book.energy[b.physical.reserve(child)],0)
        self.assertEqual(b.book.audit()['rejections'],0)

    def test_10_checkpoint_replay(self):
        s=make(expanded_food_web=True,spatial=True,metabolism=True,juvenile=True)
        for _ in range(6):s.step()
        restored=pickle.loads(pickle.dumps(s,pickle.HIGHEST_PROTOCOL))
        for _ in range(9):s.step();restored.step()
        self.assertEqual(fingerprint(s),fingerprint(restored))
        self.assertEqual(s.bridge.guild_summary(),restored.bridge.guild_summary())
        self.assertEqual(s.host.book.audit()['rejections'],0)

if __name__=='__main__':unittest.main()
