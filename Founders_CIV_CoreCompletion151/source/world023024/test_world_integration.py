import unittest
from math import isclose
from founders_civ.experimental.world_integration import IntegratedWorld
from founders_civ.experimental.social_agents import SocialSimulation


def make_realm(sim,name='Test Realm',x=65,y=45):
    s=sim.seeds
    author='F001'
    b=s.draft(author,'realm',name,x=x,y=y)
    s.research(author,b.id)
    sim.step()
    if sim.tick not in b.research_ticks:s.research(author,b.id)
    same=[a for a,f in sim.founders.people.items() if a!=author and f.location==sim.founders.people[author].location]
    if not same:raise RuntimeError('no reviewer')
    s.validate(same[0],b.id)
    return s.plant(author,b.id)

class WorldIntegrationTests(unittest.TestCase):
    def test_shared_book_and_clock(self):
        x=IntegratedWorld(101)
        self.assertIs(x.book,x.ecology.book)
        self.assertIs(x.book,x.founders.book)
        self.assertEqual(len(x.founders.people),100)
        self.assertTrue(x.founders.integrity())
        for _ in range(3):x.step()
        self.assertEqual(x.tick,x.ecology.day)
        self.assertEqual(x.counter['decision'],300)
        self.assertLess(abs(x.book.audit()['energy_error']),1e-6)

    def test_world_requires_planted_realm(self):
        s=IntegratedWorld(102)
        with self.assertRaises(ValueError):s.seeds.draft('F001','world','A world')
        self.assertEqual(s.seeds.blueprints,{})

    def test_research_requires_distinct_ticks_and_peer(self):
        s=IntegratedWorld(103)
        b=s.seeds.draft('F001','realm','Dawn',x=65,y=45)
        s.seeds.research('F001',b.id)
        with self.assertRaises(ValueError):s.seeds.research('F001',b.id)
        with self.assertRaises(ValueError):s.seeds.validate('F002',b.id)
        s.step()
        if s.tick not in b.research_ticks:s.seeds.research('F001',b.id)
        with self.assertRaises(ValueError):s.seeds.validate('F001',b.id)
        reviewer=next(a for a,f in s.founders.people.items() if a!='F001' and f.location==s.founders.people['F001'].location)
        s.seeds.validate(reviewer,b.id)
        self.assertEqual(b.stage,'validated')

    def test_actual_material_and_energy_planted(self):
        s=IntegratedWorld(104)
        base_mass=s.book.audit()['mass_total']
        c=make_realm(s)
        self.assertEqual(c['kind'],'realm')
        self.assertGreater(s.book.mass[f'construct:{c["id"]}'],0)
        self.assertAlmostEqual(s.book.audit()['mass_total'],base_mass)
        self.assertGreater(s.book.energy[f'binding:{c["id"]}'],0)
        self.assertEqual(s.book.audit()['toll_events']>=1,True)

    def test_no_unvalidated_physical_creation(self):
        s=IntegratedWorld(105)
        b=s.seeds.draft('F001','realm','Unready',x=65,y=45)
        before=s.book.mass['soil:Solara:grassland']
        with self.assertRaises(ValueError):s.seeds.plant('F001',b.id)
        self.assertEqual(s.book.mass['soil:Solara:grassland'],before)

    def test_family_planting_and_cascade(self):
        s=IntegratedWorld(106)
        realm=make_realm(s)
        world=s.seeds.draft('F001','world','A Tree',realm['id'],x=realm['x']+2,y=realm['y']+2)
        s.seeds.research('F001',world.id);s.step()
        if s.tick not in world.research_ticks:s.seeds.research('F001',world.id)
        peer=next(a for a,f in s.founders.people.items() if a!='F001' and f.location==s.founders.people['F001'].location)
        s.seeds.validate(peer,world.id);tree=s.seeds.plant('F001',world.id)
        self.assertEqual(tree['parent'],realm['id'])
        s.seeds.constructs.collapse(realm['id'])
        s.seeds.advance()
        self.assertEqual(s.seeds.plants[tree['id']]['status'],'collapsed')
        self.assertEqual(s.seeds.plants[realm['id']]['status'],'collapsed')
        s.book.audit()

    def test_repeatability(self):
        a,b=IntegratedWorld(107),IntegratedWorld(107)
        for _ in range(5):a.step();b.step()
        self.assertEqual(a.summary()['actions'],b.summary()['actions'])
        self.assertEqual(a.seeds.export(),b.seeds.export())

    def test_no_ghost_energy_after_checkpoint(self):
        s=IntegratedWorld(108)
        old=s.book.audit()['energy_total']
        s.save_checkpoint('F001')
        s.founders.learn('F001','research',.5,'new after save')
        s.kill_and_rebirth('F001')
        self.assertLess(s.founders.people['F001'].skills['research'],.9)
        self.assertEqual(s.book.audit()['energy_total'],old)

    def test_social_only_regression_compat(self):
        x=SocialSimulation(109)
        self.assertEqual(len(x.founders.people),100)
        x.step();self.assertEqual(x.counter['decision'],100)

if __name__=='__main__':unittest.main()
