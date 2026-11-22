"""C171: restored scheduler checkpoint age must be a strict integer."""
import unittest
from types import SimpleNamespace
from founders_civ.core.ledger import Book
from founders_civ.core.autonomous_provisioning import TreeProvisioningPolicy

class CheckpointAgeTests(unittest.TestCase):
    def test_invalid_last_age_never_changes_book_or_policy(self):
        for bad in (True, False, 1.0, -2, float('nan'), '1'):
            with self.subTest(bad=bad):
                book=Book();book.seed_mass('plant:river',5.);book.freeze()
                sim=SimpleNamespace(book=book,seeds=SimpleNamespace(plants={'T':{'status':'stable'}}))
                tree=SimpleNamespace(book=book,sim=sim,world_id=None,
                    habitats=('river',),age=1,state='active',id='T')
                policy=TreeProvisioningPolicy(tree)
                policy.last_age=bad
                with self.assertRaisesRegex(ValueError,'invalid Tree provisioning checkpoint age'):
                    policy.tick()
                self.assertEqual(book.seq,0)
                self.assertEqual(policy.events,[])
                self.assertEqual(policy.lots,{})
                book.audit()
    def test_valid_initial_checkpoint(self):
        book=Book();book.freeze()
        sim=SimpleNamespace(book=book,seeds=SimpleNamespace(plants={'T':{'status':'stable'}}))
        tree=SimpleNamespace(book=book,sim=sim,world_id=None,
            habitats=('river',),age=1,state='active',id='T')
        policy=TreeProvisioningPolicy(tree)
        self.assertTrue(policy.tick())
        self.assertEqual(policy.last_age,1)

if __name__=='__main__':unittest.main()
