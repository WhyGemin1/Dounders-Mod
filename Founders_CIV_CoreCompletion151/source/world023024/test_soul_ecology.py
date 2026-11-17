import unittest
from soul_ecology_v021 import EcologyTrial,RouteCognition,stage_for,safe_patch
from founders_civ.experimental.evolution import Population

class SoulEcologyTests(unittest.TestCase):
    def test_source_tagged_instruction_is_not_practice(self):
        b=RouteCognition('A')
        b.instruct(1,'cold','south','Elder')
        self.assertEqual(b.route_skill, {})
        self.assertEqual(b.episodes[0].source,'Elder')
        self.assertEqual(b.episodes[0].kind,'instruction')
        self.assertEqual(b.practiced,0)

    def test_retrieval_decreases_without_erasing_memories(self):
        b=RouteCognition('A');b.instruct(1,'cold','south','Elder')
        near=b.retrieve(1,'cold','south',decay=.12)
        far=b.retrieve(40,'cold','south',decay=.12)
        self.assertGreater(near,far)
        self.assertEqual(len(b.episodes),1)
        self.assertIn(('cold','south'),b.beliefs)

    def test_context_required_for_route_retrieval(self):
        b=RouteCognition('A');b.instruct(1,'cold','south','Elder')
        self.assertEqual(b.retrieve(2,'mild','south'),0)
        self.assertGreater(b.retrieve(2,'cold','south'),0)

    def test_direct_practice_creates_skill_and_evidence(self):
        t=EcologyTrial(seed=10,mode='full')
        b=t.brains['G00004'];o=t.pop.people['G00004']
        self.assertEqual(b.route_skill,{})
        ev=b.practice(1,'cold','south',True)
        o.soul.practice('migration',ev.id)
        self.assertGreater(b.route_skill['south'],0)
        self.assertIn(ev.id,o.soul.practiced_nodes['migration'])
        self.assertEqual(o.soul.states,{}) # No automatic State unlock

    def test_contradiction_revises_belief_and_source_trust(self):
        b=RouteCognition('A');b.instruct(1,'cold','south','Elder',quality=.95)
        c0=b.beliefs[('cold','south')].quality;t0=b.source_trust.get('Elder',.65)
        b.practice(2,'cold','south',safe=False)
        self.assertLess(b.beliefs[('cold','south')].quality,c0)
        self.assertLess(b.source_trust['Elder'],t0)
        self.assertGreater(b.revisions,0)

    def test_exact_reproducibility(self):
        a=EcologyTrial(25,mode='full').run(12)
        b=EcologyTrial(25,mode='full').run(12)
        self.assertEqual(a,b)

    def test_no_hazard_means_no_actor_migration(self):
        for mode in ('baseline','episodic','social','full'):
            result=EcologyTrial(11,mode=mode,hazard=False).run(12)
            self.assertEqual(result['migrations'],0)
            self.assertEqual(result['hazard_deaths'],0)

    def test_no_hazard_ecology_is_invariant_across_arms(self):
        results=[EcologyTrial(26,mode=m,hazard=False).run(12)
                 for m in ('baseline','episodic','social','full')]
        self.assertEqual([r['alive'] for r in results],[results[0]['alive']]*4)
        self.assertEqual([r['births'] for r in results],[results[0]['births']]*4)
        self.assertEqual([r['food_remaining'] for r in results],[results[0]['food_remaining']]*4)

    def test_original_population_biology_and_ledger_still_used(self):
        t=EcologyTrial(12,mode='full')
        self.assertIsInstance(t.pop,Population)
        a=t.run(12)['audit']
        self.assertLess(abs(a['mass_error']),1e-7)
        self.assertLess(abs(a['energy_error']),1e-7)
        self.assertEqual(t.pop.book.external,0)

    def test_newborn_does_not_inherit_route_knowledge(self):
        p=Population(seed=8,n=4,food_per_patch=100)
        parents=[x for x in p.people.values() if x.patch=='north']
        for a in parents:a.age=2;a.learned_routes.add('route:south')
        kid=p.reproduce(parents[0].id,parents[1].id)
        self.assertIsNotNone(kid)
        self.assertFalse(p.people[kid].learned_routes)
        self.assertEqual(p.people[kid].soul.practiced_nodes,{})

    def test_no_material_or_energy_from_memory_encoding(self):
        t=EcologyTrial(70,'full');before=t.pop.book.audit().copy()
        t.brains['G00002'].instruct(1,'cold','south','Elder')
        after=t.pop.book.audit()
        self.assertEqual(before['mass_total'],after['mass_total'])
        self.assertEqual(before['energy_total'],after['energy_total'])

if __name__=='__main__':unittest.main()
