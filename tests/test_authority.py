"""Integration tests require extracted Core151 engine and reconstructed M01 gateway."""
import unittest
from founders_engine.authority import SingleEngineSession
from run_world_tree_pilot import bootstrap

class SingleAuthorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world, _, cls.tree_id = bootstrap(400)

    def setUp(self):
        self.session = SingleEngineSession(self.world, self.tree_id)

    def test_one_book_and_100_founders(self):
        state = self.session.audit()
        self.assertEqual(state.founder_count, 100)
        self.assertIs(self.session.world.book, self.session.book)
        self.assertEqual(state.tree_count, 1)

    def test_reject_second_ledger(self):
        class ShadowBook:
            ledger = object()
            def snapshot(self): return {}
        with self.assertRaises(ValueError):
            self.session.attach_observer(ShadowBook())

    def test_reject_second_clock(self):
        class Clock:
            clock = 42
            def snapshot(self): return {}
        with self.assertRaises(ValueError):
            self.session.attach_observer(Clock())

    def test_accept_read_only_observer(self):
        class Observer:
            def snapshot(self): return {'source': 'synthetic'}
        self.assertEqual(
            self.session.attach_observer(Observer()).snapshot()['source'],
            'synthetic')

    def test_single_clock_and_book_audit(self):
        before = self.session.audit()
        self.session.step()
        after = self.session.audit()
        self.assertEqual(after.tick, before.tick + 1)
        self.assertEqual(after.founder_count, 100)
        self.assertLess(abs(after.book_mass_error), 1e-6)
        self.assertLess(abs(after.book_energy_error), 1e-6)

    def test_reject_invalid_founder_harvest_without_book_change(self):
        before = self.session.book.seq
        with self.assertRaises(ValueError):
            self.session.harvest('FAKE', 'invalid-source', 'r1',
                                 'forest', 'plant', .01, .001)
        self.assertEqual(self.session.book.seq, before)

    def test_detect_founder_identity_substitution(self):
        world, _, tree_id = bootstrap(401)
        session = SingleEngineSession(world, tree_id)
        founder_id = next(iter(world.founders.people))
        founder = world.founders.people.pop(founder_id)
        try:
            world.founders.people['F999'] = founder
            with self.assertRaisesRegex(RuntimeError, 'Founder identities changed'):
                session.audit()
        finally:
            world.founders.people.pop('F999', None)
            world.founders.people[founder_id] = founder

    def test_detect_founder_registry_book_swap(self):
        world, _, tree_id = bootstrap(402)
        session = SingleEngineSession(world, tree_id)
        original = world.founders.book
        try:
            world.founders.book = object()
            with self.assertRaisesRegex(RuntimeError, 'registry Book authority changed'):
                session.audit()
        finally:
            world.founders.book = original

if __name__ == '__main__':
    unittest.main()
