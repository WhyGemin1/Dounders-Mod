import unittest
from knowledge_architecture import Claim,KnowledgeWorld,Cognition,encounter,practice

class KnowledgeArchitectureTests(unittest.TestCase):
    def setUp(self):
        self.w=KnowledgeWorld();self.w.add(Claim('K','river','Technique'))
        self.c=Cognition()
    def test_encounter_is_not_application(self):
        encounter(self.w,self.c,0,'A','K','B','speech')
        self.assertEqual(self.c.claim('K').practiced,0)
        self.assertGreater(self.c.claim('K').recall,0)
    def test_no_physical_success_without_feasibility(self):
        self.assertFalse(practice(self.w,self.c,0,'A','K',1.0,False))
    def test_trust_is_directional_and_evidence_driven(self):
        a=self.c.partner('B');b=self.c.partner('C')
        a.update('integrity',False)
        self.assertLess(a.expectation('integrity'),b.expectation('integrity'))
    def test_provenance(self):
        eid=encounter(self.w,self.c,0,'A','K','B','speech')
        self.assertIn(eid,self.c.claim('K').provenance)
        self.assertEqual(self.w.events[0]['event_id'],eid)
    def test_duplicate_claim(self):
        with self.assertRaises(ValueError):self.w.add(Claim('K','river','Another'))
    def test_claim_truth_is_not_actor_accessible(self):
        self.assertNotIn('actual_validity',vars(self.c.claim('K')))
if __name__=='__main__':unittest.main()
