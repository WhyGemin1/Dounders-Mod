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

    def test_detect_same_id_founder_object_replacement(self):
        from copy import copy
        world, _, tree_id = bootstrap(403)
        session = SingleEngineSession(world, tree_id)
        founder_id = next(iter(world.founders.people))
        original = world.founders.people[founder_id]
        try:
            world.founders.people[founder_id] = copy(original)
            with self.assertRaisesRegex(RuntimeError, 'Founder object replaced'):
                session.audit()
        finally:
            world.founders.people[founder_id] = original

    def test_original_founder_reference_is_retained(self):
        world, _, tree_id = bootstrap(404)
        session = SingleEngineSession(world, tree_id)
        founder_id = next(iter(world.founders.people))
        original = world.founders.people[founder_id]
        self.assertIs(session._founder_objects[founder_id], original)
        try:
            del world.founders.people[founder_id]
            with self.assertRaisesRegex(RuntimeError, 'Founder identities changed'):
                session.audit()
            self.assertIs(session._founder_objects[founder_id], original)
        finally:
            world.founders.people[founder_id] = original

    def test_nonfinite_book_audit_fails_closed(self):
        from unittest.mock import patch
        world, _, tree_id = bootstrap(405)
        session = SingleEngineSession(world, tree_id)
        valid = world.book.audit()
        for key, invalid in (('mass_error', float('nan')),
                             ('energy_error', float('inf'))):
            broken = dict(valid)
            broken[key] = invalid
            with self.subTest(key=key), patch.object(world.book, 'audit', return_value=broken):
                with self.assertRaisesRegex(RuntimeError, 'non-finite canonical Book'):
                    session.audit()

    def test_reject_out_of_session_world_clock_change(self):
        world, _, tree_id = bootstrap(406)
        session = SingleEngineSession(world, tree_id)
        original_tick = world.tick
        try:
            world.tick += 1
            with self.assertRaisesRegex(RuntimeError, 'clock changed outside session'):
                session.audit()
            with self.assertRaisesRegex(RuntimeError, 'clock changed outside session'):
                session.step()
        finally:
            world.tick = original_tick
        session.audit()

    def test_reject_out_of_session_book_sequence_change(self):
        world, _, tree_id = bootstrap(407)
        session = SingleEngineSession(world, tree_id)
        original_seq = world.book.seq
        try:
            world.book.seq += 1
            with self.assertRaisesRegex(RuntimeError, 'Book sequence changed outside session'):
                session.audit()
            with self.assertRaisesRegex(RuntimeError, 'Book sequence changed outside session'):
                session.harvest('FAKE', 'invalid-source', 'r1',
                                'forest', 'plant', .01, .001)
        finally:
            world.book.seq = original_seq
        session.audit()
        session.step()
        self.assertEqual(session.audit().book_sequence, world.book.seq)

    def test_book_replay_receipt_must_belong_to_existing_history(self):
        from founders_civ.core.ledger import Book, Transaction
        book = Book()
        book.seed_mass('plant:source', 2.0)
        book.seed_energy('chem:source', 3.0)
        book.freeze()
        legs = (('plant:source', 'plant:founder:F001', 0.5),)
        first, applied = book.move_once('m01:test:source:r1', material=legs)
        self.assertTrue(applied)
        before = (book.seq, dict(book.mass), dict(book.energy))
        replay, applied = book.move_once('m01:test:source:r1', material=legs)
        self.assertFalse(applied)
        self.assertEqual(first, replay)
        self.assertEqual(before, (book.seq, dict(book.mass), dict(book.energy)))
        key = 'm01:test:source:r1'
        original = book.request_receipts[key]
        try:
            book.request_receipts[key] = (original[0], Transaction(
                book.seq + 1, 'move', legs, (), 0.0, 0.0))
            with self.assertRaisesRegex(ValueError, 'invalid canonical Book replay receipt'):
                book.move_once(key, material=legs)
            self.assertEqual(before, (book.seq, dict(book.mass), dict(book.energy)))
        finally:
            book.request_receipts[key] = original
        book.audit()

if __name__ == '__main__':
    unittest.main()
