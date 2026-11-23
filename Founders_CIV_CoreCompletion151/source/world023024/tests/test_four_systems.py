import unittest
from founders_civ.core.ledger import Book
from founders_civ.experimental.founders import FounderRegistry
from founders_civ.experimental.soul import SoulNetwork,AbilityOutcome
from founders_civ.experimental.evolution import Population
from founders_civ.experimental.constructs import ConstructRegistry

class FounderTests(unittest.TestCase):
    def setup_book(self,house=300):
        b=Book();b.seed_mass('background:world',0.);b.seed_mass('goods:F001:wood',4.);b.seed_energy('house',house);b.freeze();return b
    def test_100_founders_partnered_no_self(self):
        r=FounderRegistry(self.setup_book());self.assertTrue(r.integrity())
        self.assertEqual(len({tuple(sorted((p.id,p.partner_id))) for p in r.people.values()}),50)
    def test_checkpoint_rolls_back_unsaved_development(self):
        b=self.setup_book();r=FounderRegistry(b);f=r.people['F001']
        r.learn(f.id,'craft',2,'old experience');r.checkpoint(f.id)
        r.learn(f.id,'craft',3,'unsaved experience');f.inventory['wood']=4
        f.location='world';self.assertTrue(r.die(f.id))
        self.assertEqual(f.skills['craft'],2);self.assertEqual(f.memories,['old experience'])
        self.assertEqual(f.location,'house');self.assertFalse(f.inventory)
        self.assertEqual(b.mass['goods:dropped:world:wood'],4.)
        b.audit()
    def test_cannot_checkpoint_away_from_house(self):
        r=FounderRegistry(self.setup_book());r.people['F001'].location='world'
        with self.assertRaises(ValueError):r.checkpoint('F001')
    def test_unfunded_rebirth_is_pending_not_dead_permanently(self):
        b=self.setup_book(0);r=FounderRegistry(b)
        self.assertFalse(r.die('F001'));self.assertFalse(r.people['F001'].alive)
        b.wellspring(4)
        self.assertTrue(r.rebirth('F001'));self.assertTrue(r.people['F001'].alive)
        b.audit()

class SoulTests(unittest.TestCase):
    def build_net(self):
        s=SoulNetwork('actor1',intrinsic_mode=7)
        for i in range(12):
            n=f'n{i}'
            s.practice(n,f'{n}:a');s.practice(n,f'{n}:b')
            s.develop_state(f's{i}',[n],.6)
        return s
    def test_twelve_temple_modes_validated(self):
        with self.assertRaises(ValueError):SoulNetwork('x',12)
    def test_kingdom_nation_realm_thresholds(self):
        s=self.build_net()
        s.kingdom('k1',['s0','s1','s2'],[('s0','s1'),('s1','s2')])
        s.kingdom('k2',['s3','s4','s5'],[('s3','s4'),('s4','s5')])
        s.kingdom('k3',['s6','s7','s8'],[('s6','s7'),('s7','s8')])
        s.kingdom('k4',['s9','s10','s11'],[('s9','s10'),('s10','s11')])
        s.nation('n1',['s1','s3','s6','s10'])
        with self.assertRaises(ValueError):s.realm('r',['k1','k2','k3','k4'])
        s.earn_emperor(['n0:a','n1:a','n2:a','n3:a'])
        s.realm('r',['k1','k2','k3','k4'])
        self.assertEqual(len(s.realms['r']),4)
    def test_incompatible_kingdom_rejected(self):
        s=self.build_net()
        with self.assertRaises(ValueError):s.kingdom('k',['s0','s1','s2'],[('s0','s1')])
    def test_vow_breach_blocks_state(self):
        s=SoulNetwork('x');s.make_vow('v','protect grove')
        s.validate_vow('v','witness_record');s.practice('guard','g1');s.practice('guard','g2')
        s.develop_state('vigil',['guard'],.8,vow_id='v')
        s.breach_vow('v','explicit_harm_event')
        with self.assertRaises(ValueError):s.activate('vigil',1,1,2)
    def test_practice_needed_not_belief_only(self):
        s=SoulNetwork('x');s.make_vow('v','save others');s.validate_vow('v','witness')
        with self.assertRaises(ValueError):s.develop_state('vigil',['guard'],.8,vow_id='v')
    def test_safe_failure_and_exceptional_overload(self):
        s=self.build_net()
        self.assertEqual(s.activate('s0',3,2,4),AbilityOutcome.REJECTED)
        self.assertEqual(s.activate('s0',2,2,4),AbilityOutcome.REJECTED) # No free energy without a ledger
        self.assertEqual(s.activate('s0',100,2,4),AbilityOutcome.OVERLOAD)
        b=Book();b.seed_mass('background:world',0.);b.seed_energy('actor:soul',9);b.freeze()
        self.assertEqual(s.activate('s0',2,2,3,ledger=b,source='actor:soul'),AbilityOutcome.SUCCESS)
        self.assertEqual(b.energy['actor:soul'],7);b.audit()

class EvolutionTests(unittest.TestCase):
    def test_birth_carries_genes_but_not_routes(self):
        p=Population(seed=5,n=4)
        x,y=list(p.people.values())[:2]
        y.patch=x.patch;x.age=y.age=2;x.learned_routes.add('route:south')
        z=p.reproduce(x.id,y.id)
        self.assertIsNotNone(z)
        self.assertEqual(p.people[z].learned_routes,set())
        self.assertEqual(p.people[z].parents,(x.id,y.id))
        p.book.audit()
    def test_social_learning_requires_contact(self):
        p=Population(seed=6,n=4)
        a,b=list(p.people.values())[:2]
        a.learned_routes.add('route:north');self.assertFalse(p.teach(a.id,b.id,'route:north'))
        b.patch=a.patch
        # deterministic chance over repeated encounters, not guaranteed in one
        self.assertTrue(any(p.teach(a.id,b.id,'route:north') for _ in range(20)))
    def test_birth_death_material_accounts(self):
        p=Population(seed=9,n=4)
        a,b=list(p.people.values())[:2];b.patch=a.patch;a.age=b.age=2
        n=p.reproduce(a.id,b.id)
        food_before=p.book.mass[f'food:{a.patch}'];p.die(n,'mortality')
        self.assertEqual(p.book.mass[f'food:{a.patch}'],food_before)
        self.assertAlmostEqual(p.book.mass[f'dead:{a.patch}'],1.)
        p.book.audit()
    def test_generation_audit_and_selection(self):
        p=Population(seed=13,n=30)
        for _ in range(8):p.step(climate='cold')
        summary=p.summary()
        self.assertGreater(summary['births'],0)
        self.assertLess(abs(summary['mass_audit']['mass_error']),1e-6)
        self.assertLess(abs(summary['mass_audit']['energy_error']),1e-6)

class ConstructTests(unittest.TestCase):
    def setup(self,house=60):
        b=Book();b.seed_mass('stone:world',20.);b.seed_energy('house',house)
        b.seed_energy('world_work',100);b.freeze();return b
    def test_funded_maintenance_no_toll(self):
        b=self.setup();r=ConstructRegistry(b)
        c=r.build('d1','dimension','world_A','stone:world',5,1.0,5)
        tolls=b.toll_count
        for _ in range(3):r.tick('d1')
        self.assertEqual(b.toll_count,tolls)
        self.assertEqual(c.status,'stable');b.audit()
    def test_starvation_collapses_once_and_preserves_mass_energy(self):
        b=self.setup();r=ConstructRegistry(b)
        c=r.build('d1','dimension','world_A','stone:world',5,1,0,collapse_to='mist')
        for _ in range(5):r.tick('d1')
        self.assertEqual(c.status,'collapsed')
        self.assertEqual(b.mass['mist:d1'],5)
        self.assertEqual(b.toll_count,2) # 1 build, 1 collapse
        r.tick('d1');self.assertEqual(b.toll_count,2)
        b.audit()
    def test_topup_can_prevent_collapse(self):
        b=self.setup();r=ConstructRegistry(b)
        c=r.build('s1','construct','world_A','stone:world',2,1,0)
        r.top_up('s1',6)
        for _ in range(5):r.tick('s1')
        self.assertEqual(c.status,'stable');b.audit()
    def test_build_refuses_unfunded_energy(self):
        b=self.setup(house=1);r=ConstructRegistry(b)
        with self.assertRaises(ValueError):r.build('d','dimension','world','stone:world',5,1,8)
        b.audit()

if __name__=='__main__': unittest.main()

class CrossSystemTests(unittest.TestCase):
    def test_checkpoint_restores_saved_soul_experiences(self):
        b=Book();b.seed_mass('world:marker',0);b.seed_energy('house',30);b.freeze()
        r=FounderRegistry(b)
        f=r.people['F001'];f.soul.practice('craft','saved-practice')
        r.checkpoint(f.id)
        f.soul.practice('craft','unsaved-practice')
        f.location='world';r.die(f.id)
        self.assertEqual(f.soul.practiced_nodes['craft'],{'saved-practice'})
        b.audit()
    def test_animal_teaching_creates_soul_experience(self):
        p=Population(seed=22,n=4)
        a,b=list(p.people.values())[:2];b.patch=a.patch
        a.learned_routes.add('route:south')
        for _ in range(20):
            if p.teach(a.id,b.id,'route:south'):break
        self.assertIn('migration',b.soul.practiced_nodes)
        self.assertEqual(len(b.soul.practiced_nodes['migration']),1)
        p.book.audit()
