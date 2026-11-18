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

    def test_m01_gateway_authority_binding_cannot_be_replaced(self):
        """The adapter must not be rebound to a different resource authority."""
        world, _, tree_id = bootstrap(420)
        session = SingleEngineSession(world, tree_id)
        gateway = session.gateway
        original_book = gateway.book
        try:
            gateway.book = object()
            with self.assertRaisesRegex(RuntimeError, 'M01 gateway authority changed'):
                session.audit()
            with self.assertRaisesRegex(RuntimeError, 'M01 gateway authority changed'):
                session.step()
            with self.assertRaisesRegex(RuntimeError, 'M01 gateway authority changed'):
                session.harvest('F001', 'source', 'r1', 'forest', 'plant', .01, .001)
        finally:
            gateway.book = original_book
        session.audit()
        try:
            session.gateway = object()
            with self.assertRaisesRegex(RuntimeError, 'M01 gateway authority changed'):
                session.audit()
        finally:
            session.gateway = gateway
        session.audit()

    def test_missing_authoritative_tree_fails_closed(self):
        """Deleting the original Tree cannot silently fall through to KeyError."""
        world, _, tree_id = bootstrap(421)
        session = SingleEngineSession(world, tree_id)
        original = world.world_trees.worlds.pop(tree_id)
        try:
            for operation in (
                session.audit,
                session.step,
                lambda: session.harvest('F001', 'source', 'r1',
                                        'forest', 'plant', .01, .001),
            ):
                with self.assertRaisesRegex(RuntimeError, 'authoritative World Tree removed'):
                    operation()
        finally:
            world.world_trees.worlds[tree_id] = original
        session.audit()

    def test_founder_registry_object_substitution_fails_closed(self):
        """A shallow copy with the same actors and Book is not the authority."""
        from copy import copy
        world, _, tree_id = bootstrap(423)
        session = SingleEngineSession(world, tree_id)
        original = world.founders
        replacement = copy(original)
        self.assertIs(replacement.book, world.book)
        self.assertIs(replacement.people, original.people)
        try:
            world.founders = replacement
            for operation in (
                session.audit,
                session.step,
                lambda: session.harvest('FAKE', 'invalid-source', 'r1',
                                        'forest', 'plant', .01, .001),
            ):
                with self.assertRaisesRegex(RuntimeError, 'Founder registry object replaced'):
                    operation()
        finally:
            world.founders = original
        session.audit()

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

    def test_m01_harvest_preflight_rejects_finite_conservation_drift(self):
        """A corrupt canonical Book cannot fund even a synthetic M01 harvest."""
        from unittest.mock import patch
        world, _, tree_id = bootstrap(418)
        session = SingleEngineSession(world, tree_id)
        valid = world.book.audit()
        before_tick, before_seq = world.tick, world.book.seq
        before_receipts = dict(world.book.request_receipts)
        for key in ('mass_error', 'energy_error'):
            broken = dict(valid)
            broken[key] = 0.001
            with self.subTest(key=key):
                with patch.object(world.book, 'audit', return_value=broken):
                    with patch.object(session.gateway, 'founder_harvest') as gateway:
                        with self.assertRaisesRegex(RuntimeError, 'conservation drift exceeds tolerance'):
                            session.harvest('F001', 'source', 'r1',
                                            'forest', 'plant', .01, .001)
                        gateway.assert_not_called()
                self.assertEqual((world.tick, world.book.seq), (before_tick, before_seq))
                self.assertEqual(world.book.request_receipts, before_receipts)
        session.audit()

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

    def test_reject_world_tree_object_substitution(self):
        """Same registry key and shared Book must not permit a new Tree actor."""
        from copy import copy
        world, _, tree_id = bootstrap(419)
        session = SingleEngineSession(world, tree_id)
        original = world.world_trees.worlds[tree_id]
        replacement = copy(original)
        self.assertIsNot(replacement, original)
        self.assertIs(replacement.book, world.book)
        self.assertIs(replacement.sim, world)
        try:
            world.world_trees.worlds[tree_id] = replacement
            with self.assertRaisesRegex(RuntimeError, 'World Tree object replaced'):
                session.audit()
            with self.assertRaisesRegex(RuntimeError, 'World Tree object replaced'):
                session.step()
            with self.assertRaisesRegex(RuntimeError, 'World Tree object replaced'):
                session.harvest('FAKE', 'invalid-source', 'r1',
                                'forest', 'plant', .01, .001)
        finally:
            world.world_trees.worlds[tree_id] = original
        session.audit()

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

    def test_invalid_conservation_audit_types_block_step_and_harvest(self):
        """A Boolean or string is not a physical Book conservation residual."""
        from unittest.mock import patch
        world, _, tree_id = bootstrap(422)
        session = SingleEngineSession(world, tree_id)
        valid = world.book.audit()
        before = (world.tick, world.book.seq)
        for key, value in (('mass_error', True), ('energy_error', '0.0')):
            broken = dict(valid)
            broken[key] = value
            with self.subTest(key=key), patch.object(world.book, 'audit', return_value=broken):
                with patch.object(world, 'step') as step:
                    with self.assertRaisesRegex(RuntimeError, 'invalid canonical Book conservation audit type'):
                        session.step()
                    step.assert_not_called()
                with patch.object(session.gateway, 'founder_harvest') as gateway:
                    with self.assertRaisesRegex(RuntimeError, 'invalid canonical Book conservation audit type'):
                        session.harvest('F001', 'source', 'r1', 'forest', 'plant', .01, .001)
                    gateway.assert_not_called()
            self.assertEqual((world.tick, world.book.seq), before)
        session.audit()

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

    def test_incomplete_conservation_audit_fails_closed(self):
        """Missing audit fields must reject both live mutations without KeyError."""
        from unittest.mock import patch
        world, _, tree_id = bootstrap(424)
        session = SingleEngineSession(world, tree_id)
        before = (world.tick, world.book.seq)
        for proof in ({'mass_error': 0.0}, {'energy_error': 0.0}, None):
            with self.subTest(proof=proof), patch.object(
                    world.book, 'audit', return_value=proof), patch.object(
                    world, 'step') as advance, patch.object(
                    session.gateway, 'founder_harvest') as settle:
                with self.assertRaisesRegex(RuntimeError, 'incomplete canonical Book'):
                    session.step()
                with self.assertRaisesRegex(RuntimeError, 'incomplete canonical Book'):
                    session.harvest('F001', 'source', 'r1', 'forest', 'plant', .01, .001)
                advance.assert_not_called()
                settle.assert_not_called()
            self.assertEqual((world.tick, world.book.seq), before)
        session.audit()

    def test_failed_world_step_quarantines_session(self):
        from unittest.mock import patch
        world, _, tree_id = bootstrap(408)
        session = SingleEngineSession(world, tree_id)
        before = world.tick

        def partial_step():
            world.tick += 1
            raise OSError('injected mid-step failure')

        with patch.object(world, 'step', side_effect=partial_step):
            with self.assertRaisesRegex(OSError, 'mid-step failure'):
                session.step()
        self.assertEqual(world.tick, before + 1)
        with self.assertRaisesRegex(RuntimeError, 'step outcome uncertain'):
            session.audit()
        with self.assertRaisesRegex(RuntimeError, 'step outcome uncertain'):
            session.step()
        with self.assertRaisesRegex(RuntimeError, 'step outcome uncertain'):
            session.harvest('FAKE', 'invalid-source', 'r1',
                            'forest', 'plant', .01, .001)

    def test_failed_step_with_book_mutation_but_no_clock_advance_quarantines(self):
        """An interrupted real step must fail closed even if its tick never advances."""
        from unittest.mock import patch
        world, _, tree_id = bootstrap(415)
        session = SingleEngineSession(world, tree_id)
        before_tick, before_seq = world.tick, world.book.seq
        key = 'plant:injected-step-failure'
        original = world.book.mass.get(key)

        def partial_step():
            world.book.mass[key] = world.book.mass.get(key, 0.0) + 0.25
            raise OSError('injected pre-clock world-step failure')

        try:
            with patch.object(world, 'step', side_effect=partial_step):
                with self.assertRaisesRegex(OSError, 'pre-clock world-step failure'):
                    session.step()
            self.assertEqual(world.tick, before_tick)
            self.assertEqual(world.book.seq, before_seq)
            with self.assertRaisesRegex(RuntimeError, 'step outcome uncertain'):
                session.audit()
            with self.assertRaisesRegex(RuntimeError, 'step outcome uncertain'):
                session.step()
            with self.assertRaisesRegex(RuntimeError, 'step outcome uncertain'):
                session.harvest('FAKE', 'invalid-source', 'r1',
                                'forest', 'plant', .01, .001)
        finally:
            if original is None:
                world.book.mass.pop(key, None)
            else:
                world.book.mass[key] = original

    def test_failed_harvest_after_book_mutation_quarantines_session(self):
        from unittest.mock import patch
        world, _, tree_id = bootstrap(409)
        session = SingleEngineSession(world, tree_id)
        before = world.book.seq

        def partial_harvest(*args, **kwargs):
            world.book.seq += 1
            raise OSError('injected post-mutation harvest failure')

        with patch.object(session.gateway, 'founder_harvest',
                          side_effect=partial_harvest):
            with self.assertRaisesRegex(OSError, 'post-mutation harvest failure'):
                session.harvest('F001', 'source', 'r1',
                                'forest', 'plant', .01, .001)
        self.assertEqual(world.book.seq, before + 1)
        with self.assertRaisesRegex(RuntimeError, 'checkpoint outcome uncertain'):
            session.audit()
        with self.assertRaisesRegex(RuntimeError, 'checkpoint outcome uncertain'):
            session.step()

    def test_harvest_failure_without_sequence_advance_quarantines(self):
        from unittest.mock import patch
        world, _, tree_id = bootstrap(411)
        session = SingleEngineSession(world, tree_id)
        before = world.book.seq
        with patch.object(session.gateway, 'founder_harvest',
                          side_effect=OSError('injected pre-sequence failure')):
            with self.assertRaisesRegex(OSError, 'pre-sequence failure'):
                session.harvest('F001', 'source', 'r1',
                                'forest', 'plant', .01, .001)
        self.assertEqual(world.book.seq, before)
        with self.assertRaisesRegex(RuntimeError, 'checkpoint outcome uncertain'):
            session.audit()
        with self.assertRaisesRegex(RuntimeError, 'checkpoint outcome uncertain'):
            session.step()

    def test_value_error_after_book_balance_mutation_quarantines(self):
        from unittest.mock import patch
        world, _, tree_id = bootstrap(412)
        session = SingleEngineSession(world, tree_id)
        before_seq = world.book.seq
        key = 'plant:injected-uncommitted'
        original = world.book.mass.get(key, 0.0)

        def partial_validation(*args, **kwargs):
            world.book.mass[key] = original + 0.25
            raise ValueError('injected mutation before rejected request')

        try:
            with patch.object(session.gateway, 'founder_harvest',
                              side_effect=partial_validation):
                with self.assertRaisesRegex(ValueError, 'injected mutation'):
                    session.harvest('F001', 'source', 'r1',
                                    'forest', 'plant', .01, .001)
            self.assertEqual(world.book.seq, before_seq)
            with self.assertRaisesRegex(RuntimeError, 'checkpoint outcome uncertain'):
                session.audit()
            with self.assertRaisesRegex(RuntimeError, 'checkpoint outcome uncertain'):
                session.step()
        finally:
            if original == 0.0:
                world.book.mass.pop(key, None)
            else:
                world.book.mass[key] = original

    def test_nested_receipt_mutation_on_rejected_harvest_quarantines(self):
        from unittest.mock import patch
        world, _, tree_id = bootstrap(413)
        session = SingleEngineSession(world, tree_id)
        # Synthetic nested receipt fixture probes the snapshot guard only.
        key = 'injected:nested-receipt'
        receipt = {'nested': ['before']}
        world.book.request_receipts[key] = receipt
        try:
            def corrupt_then_reject(*args, **kwargs):
                receipt['nested'].append('after')
                raise ValueError('injected nested receipt mutation')

            with patch.object(session.gateway, 'founder_harvest',
                              side_effect=corrupt_then_reject):
                with self.assertRaisesRegex(ValueError, 'nested receipt mutation'):
                    session.harvest('F001', 'source', 'r1',
                                    'forest', 'plant', .01, .001)
            with self.assertRaisesRegex(RuntimeError, 'checkpoint outcome uncertain'):
                session.audit()
        finally:
            world.book.request_receipts.pop(key, None)

    def test_invalid_harvest_does_not_quarantine_clean_session(self):
        world, _, tree_id = bootstrap(410)
        session = SingleEngineSession(world, tree_id)
        before = world.book.seq
        with self.assertRaises(ValueError):
            session.harvest('FAKE', 'invalid-source', 'r1',
                            'forest', 'plant', .01, .001)
        self.assertEqual(world.book.seq, before)
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

    def test_finite_conservation_drift_blocks_real_world_step(self):
        """A finite but materially unbalanced Book must fail before a real tick."""
        from unittest.mock import patch
        world, _, tree_id = bootstrap(417)
        session = SingleEngineSession(world, tree_id)
        before_tick, before_seq = world.tick, world.book.seq
        for key in ('mass_error', 'energy_error'):
            with self.subTest(key=key):
                proof = dict(world.book.audit())
                proof[key] = 0.25
                with patch.object(world.book, 'audit', return_value=proof), \
                     patch.object(world, 'step') as advance:
                    with self.assertRaisesRegex(RuntimeError, 'conservation drift exceeds tolerance'):
                        session.step()
                    advance.assert_not_called()
                self.assertEqual((world.tick, world.book.seq),
                                 (before_tick, before_seq))
        session.audit()

    def test_failed_preflight_book_audit_does_not_advance_world(self):
        from unittest.mock import patch
        world, _, tree_id = bootstrap(416)
        session = SingleEngineSession(world, tree_id)
        before_tick = world.tick
        before_seq = world.book.seq
        with patch.object(world.book, 'audit', return_value={
            'mass_error': float('nan'), 'energy_error': 0.0,
        }), patch.object(world, 'step') as advance:
            with self.assertRaisesRegex(RuntimeError, 'non-finite canonical Book conservation audit'):
                session.step()
            advance.assert_not_called()
        self.assertEqual(world.tick, before_tick)
        self.assertEqual(world.book.seq, before_seq)
        session.audit()

    def test_reject_invalid_canonical_book_sequence_types(self):
        world, _, tree_id = bootstrap(414)
        session = SingleEngineSession(world, tree_id)
        original = world.book.seq
        for invalid in (True, False, -1, 0.5):
            with self.subTest(invalid=invalid):
                try:
                    world.book.seq = invalid
                    with self.assertRaisesRegex(RuntimeError, 'invalid canonical Book sequence'):
                        session.audit()
                    with self.assertRaisesRegex(RuntimeError, 'invalid canonical Book sequence'):
                        session.step()
                    with self.assertRaisesRegex(RuntimeError, 'invalid canonical Book sequence'):
                        session.harvest('FAKE', 'invalid-source', 'r1',
                                        'forest', 'plant', .01, .001)
                finally:
                    world.book.seq = original
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

    def test_world_tree_registry_object_substitution_fails_closed(self):
        """A copied registry is not the authoritative living Tree registry."""
        from copy import copy
        world, _, tree_id = bootstrap(425)
        session = SingleEngineSession(world, tree_id)
        original = world.world_trees
        before = (world.tick, world.book.seq)
        try:
            world.world_trees = copy(original)
            for operation in (
                session.audit,
                session.step,
                lambda: session.harvest('F001', 'source', 'r1',
                                        'forest', 'plant', .01, .001),
            ):
                with self.assertRaisesRegex(
                        RuntimeError, 'authoritative World Tree registry object replaced'):
                    operation()
            self.assertEqual((world.tick, world.book.seq), before)
        finally:
            world.world_trees = original
        session.audit()

if __name__ == '__main__':
    unittest.main()
