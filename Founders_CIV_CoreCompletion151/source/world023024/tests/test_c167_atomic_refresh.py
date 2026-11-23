"""C167: multi-lot refresh failure must restore Book and local policy records."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from founders_civ.core.ledger import Book
from founders_civ.core.autonomous_provisioning import TreeProvisioningPolicy, ProvisionedLot

class AtomicRefreshTests(unittest.TestCase):
    def test_later_decay_failure_rolls_back_earlier_lot(self):
        book=Book()
        book.seed_mass('portable_food:source', 1.0)
        book.freeze()
        tree=SimpleNamespace(book=book,sim=SimpleNamespace(book=book),
            world_id=None,habitats=('river',),age=20,state='collapsed',id='TREE-C167')
        policy=TreeProvisioningPolicy(tree)
        lot='C003-TREE-C167-food-0'
        policy.lots[lot]=ProvisionedLot('food','river',0)
        def interrupted_refresh():
            book.move(material=[('portable_food:source','portable_food:dest',.2)],
                      operation_id='c167-decay')
            policy.lots[lot].state='decayed'
            policy.events.append(('decay',lot,20))
            raise ValueError('second lot failed')
        with patch.object(policy,'_refresh',side_effect=interrupted_refresh):
            with self.assertRaisesRegex(ValueError,'second lot failed'):
                policy.tick()
        self.assertEqual(policy.last_age,-1)
        self.assertEqual(policy.lots[lot].state,'stored')
        self.assertEqual(policy.events,[])
        self.assertEqual(book.seq,0)
        self.assertEqual(book.mass['portable_food:source'],1.)
        self.assertEqual(book.mass['portable_food:dest'],0.)
        self.assertNotIn('c167-decay',book.operations)
        book.audit()

if __name__=='__main__':
    unittest.main()
