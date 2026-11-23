"""WORLD-023 targeted tests: actual ledger, species prerequisite and autonomy."""
import unittest
from copy import deepcopy
from types import MethodType
from founders_civ.experimental.world_integration import IntegratedWorld
from founders_civ.experimental.world_trees import BIOMES, WorldTree
from run_world_tree_pilot import bootstrap


class WorldTreeTests(unittest.TestCase):
    def test_four_habitats_and_unique_residents(self):
        s,r,w=bootstrap(400);t=s.world_trees.worlds[w]
        self.assertEqual(set(t.habitats),set(BIOMES))
        self.assertEqual(t.population,16)
        self.assertEqual(len(set(t.residents)),16)
        self.assertEqual(len(t.species_seed_ids),1)
        self.assertTrue(all(v.world==w and v.habitat in BIOMES for v in t.residents.values()))

    def test_living_tree_resources_exist_in_shared_book(self):
        s,r,w=bootstrap(400);t=s.world_trees.worlds[w]
        self.assertIs(t.book,s.ecology.book)
        for biome in BIOMES:
            self.assertGreater(s.book.mass[t.acct('soil',biome)],0)
            self.assertGreater(s.book.mass[t.acct('plant',biome)],0)
            self.assertGreater(s.book.mass[t.acct('water',biome)],0)
            self.assertGreater(s.book.energy[t.acct('chem',biome)],0)
        self.assertLess(abs(s.book.audit()['mass_error']),1e-6)

    def test_world_does_not_spawn_species_automatically(self):
        s=IntegratedWorld(409)
        b=s.seeds.draft('F001','realm','Origin Realm',x=64,y=42)
        s.seeds.research('F001',b.id);s.step()
        if s.tick not in b.research_ticks:s.seeds.research('F001',b.id)
        reviewer=next(a for a,f in s.founders.people.items()
                      if a!='F001' and f.location==s.founders.people['F001'].location)
        s.seeds.validate(reviewer,b.id);realm=s.seeds.plant('F001',b.id)
        author=max(s.founders.people,key=lambda a:(s.book.energy[f'founder:{a}'],a))
        b2=s.seeds.draft(author,'world','Unpopulated Tree',realm['id'],x=66,y=43)
        s.seeds.research(author,b2.id);s.step()
        if s.tick not in b2.research_ticks:s.seeds.research(author,b2.id)
        reviewer=next(a for a,f in s.founders.people.items()
                      if a!=author and f.location==s.founders.people[author].location)
        s.seeds.validate(reviewer,b2.id);world=s.seeds.plant(author,b2.id)
        t=s.world_trees.worlds[world['id']]
        self.assertEqual(t.state,'germinating')
        self.assertEqual(t.population,0)
        self.assertEqual(t.residents,{})
        s.step();self.assertEqual(t.population,0)

    def test_seed_requires_independent_validation(self):
        s=IntegratedWorld(400)
        with self.assertRaises(ValueError):s.seeds.draft('F001','world','Missing Realm')
        b=s.seeds.draft('F001','realm','Unreviewed Realm',x=64,y=42)
        with self.assertRaises(ValueError):s.seeds.plant('F001',b.id)

    def test_species_cannot_be_added_twice_in_first_pilot(self):
        s,r,w=bootstrap(400)
        with self.assertRaises(ValueError):s.world_trees.worlds[w].preflight_species()

    def test_climate_circulates_conserved_water(self):
        s,r,w=bootstrap(400);t=s.world_trees.worlds[w]
        before=t.timeline[-1]['water'];plant=t.timeline[-1]['plants']
        for _ in range(13):s.step()
        self.assertAlmostEqual(before,t.timeline[-1]['water'],places=6)
        self.assertNotAlmostEqual(plant,t.timeline[-1]['plants'],places=3)
        self.assertEqual(t.age,s.tick-2)
        s.book.audit()

    def test_birth_and_mortality_by_physical_rules(self):
        s,r,w=bootstrap(400);t=s.world_trees.worlds[w]
        for _ in range(35):s.step()
        self.assertGreater(t.counters['tree_birth'],0)
        self.assertTrue(any(v.generation>0 for v in t.residents.values()))
        self.assertTrue(all(v.habitat in BIOMES for v in t.residents.values()))

    def test_observation_requires_an_access_point(self):
        s,r,w=bootstrap(400);t=s.world_trees.worlds[w]
        actor=s.seeds.plants[w]['owner'];f=s.founders.people[actor]
        f.location='ridge'
        with self.assertRaises(ValueError):t.observe(actor)
        f.location='house'
        report=t.observe(actor)
        self.assertEqual(report['population'],t.population)
        self.assertIn(actor,t.observations)

    def test_study_requires_recent_observation(self):
        s,r,w=bootstrap(400);t=s.world_trees.worlds[w]
        actor='F020'  # not the autonomous World Tree steward
        with self.assertRaises(ValueError):t.study(actor)
        s.founders.people[actor].location='house'
        t.observe(actor)
        result=t.study(actor)
        self.assertGreater(result['skill_gain'],0)

    def test_autonomous_founder_observes_and_maintains(self):
        s,r,w=bootstrap(400);t=s.world_trees.worlds[w]
        for _ in range(35):s.step()
        self.assertGreater(t.counters['tree_observed'],0)
        self.assertGreater(t.counters['tree_researched'],0)
        self.assertGreater(s.counter['creation_autonomous_stewardship'],0)
        self.assertEqual(s.seeds.plants[r]['status'],'stable')
        self.assertEqual(s.seeds.plants[w]['status'],'stable')
        selected=[e for e in s.events if e['action']=='decision' and e['chosen'] in ('tree_observe','tree_research','creation_steward')]
        self.assertGreater(len(selected),0)

    def test_collapse_of_parent_archives_world_and_residents(self):
        s,r,w=bootstrap(400);t=s.world_trees.worlds[w]
        s.seeds.constructs.collapse(r)
        s.seeds.advance()
        self.assertEqual(s.seeds.plants[w]['status'],'collapsed')
        self.assertEqual(t.state,'archived')
        self.assertEqual(t.population,0)
        self.assertGreater(s.book.mass[f'remnant:tree:{w}:forest'],0)
        self.assertEqual(s.book.mass[t.acct('plant','forest')],0)
        s.book.audit()

    def test_checkpoint_rebirth_does_not_erase_world(self):
        s,r,w=bootstrap(400);tree=s.world_trees.worlds[w]
        creator=s.seeds.plants[w]['owner']
        old_age=tree.age
        s.kill_and_rebirth(creator)
        self.assertEqual(s.seeds.plants[w]['status'],'stable')
        self.assertEqual(tree.age,old_age)
        self.assertEqual(tree.population,16)
        s.book.audit()

    def test_seeded_repeatability(self):
        a,ar,aw=bootstrap(400);b,br,bw=bootstrap(400)
        for _ in range(10):a.step();b.step()
        self.assertEqual(a.world_trees.worlds[aw].timeline,b.world_trees.worlds[bw].timeline)
        self.assertEqual(a.seeds.export(),b.seeds.export())
        self.assertEqual(a.book.audit()['transactions'],b.book.audit()['transactions'])

    def test_no_maintenance_has_real_negative_consequence(self):
        s,r,w=bootstrap(400)
        policy=s._proposals
        def without_stewardship(self,a,contacts):
            return [p for p in policy(a,contacts) if p[1] not in ('creation_steward','tree_tend','seed_tend')]
        s._proposals=MethodType(without_stewardship,s)
        for _ in range(35):s.step()
        self.assertEqual(s.seeds.plants[r]['status'],'collapsed')
        self.assertEqual(s.seeds.plants[w]['status'],'collapsed')
        self.assertEqual(s.world_trees.worlds[w].population,0)
        s.book.audit()

    def test_manual_tree_api_uses_same_runtime(self):
        from launch_founder_world import App
        app=App(400)
        s,r,w=bootstrap(400)
        app.sim=s
        actor=s.seeds.plants[w]['owner']
        s.founders.people[actor].location='house'
        report=app.action({'action':'tree_observe','actor':actor,'creation_id':w})
        self.assertEqual(report['population'],s.world_trees.worlds[w].population)
        res=app.action({'action':'tree_research','actor':actor,'creation_id':w})
        self.assertGreater(res['skill_gain'],0)


if __name__=='__main__':unittest.main()
