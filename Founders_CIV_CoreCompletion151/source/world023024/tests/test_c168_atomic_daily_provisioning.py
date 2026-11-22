"""C168: refresh and multi-habitat allocation are one retryable Book day."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from founders_civ.core.ledger import Book
from founders_civ.core.autonomous_provisioning import TreeProvisioningPolicy, ProvisionedLot

class AtomicDailyProvisioningTests(unittest.TestCase):
    def test_second_allocation_failure_rolls_back_first_and_refresh(self):
        book=Book()
        book.seed_mass('portable_food:source', 2.)
        book.freeze()
        seeds=SimpleNamespace(plants={'TREE-C168': {'status':'stable'}})
        sim=SimpleNamespace(book=book,seeds=seeds)
        tree=SimpleNamespace(book=book,sim=sim,world_id=None,
            habitats=('river',),age=1,state='active',id='TREE-C168')
        policy=TreeProvisioningPolicy(tree,food_period=1,fruit_period=1)
        old_lot='C003-TREE-C168-food-0'
        policy.lots[old_lot]=ProvisionedLot('food','river',0)
        def refresh():
            policy.lots[old_lot].state='transferred'
            policy.events.append(('refresh',old_lot,1))
            book.move(material=[('portable_food:source','portable_food:refresh',.2)],
                      operation_id='c168-refresh')
        def allocate(kind,biome):
            if kind=='fruit':
                raise ValueError('fruit allocation interrupted')
            book.move(material=[('portable_food:source','portable_food:food',.3)],
                      operation_id='c168-food')
            lot='C003-TREE-C168-food-1'
            policy.lots[lot]=ProvisionedLot('food',biome,1)
            policy.events.append(('grow',lot,1))
            return True
        with patch.object(policy,'_refresh',side_effect=refresh), patch.object(
                policy,'_allocate',side_effect=allocate):
            with self.assertRaisesRegex(ValueError,'fruit allocation interrupted'):
                policy.tick()
        self.assertEqual(policy.last_age,-1)
        self.assertEqual(list(policy.lots),[old_lot])
        self.assertEqual(policy.lots[old_lot].state,'stored')
        self.assertEqual(policy.events,[])
        self.assertEqual(book.seq,0)
        self.assertEqual(book.mass['portable_food:source'],2.)
        self.assertNotIn('c168-refresh',book.operations)
        self.assertNotIn('c168-food',book.operations)
        book.audit()
        # The same age must remain eligible for deterministic retry.
        with patch.object(policy,'_refresh',return_value=None), patch.object(
                policy,'_allocate',return_value=True):
            self.assertTrue(policy.tick())
        self.assertEqual(policy.last_age,1)

if __name__=='__main__':
    unittest.main()
