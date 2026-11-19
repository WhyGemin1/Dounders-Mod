"""Regression for M01 receipt identity control characters on actual Core151."""
import unittest
from run_world_tree_pilot import bootstrap
from founders_engine.authority import SingleEngineSession


class M01IdentityControlTests(unittest.TestCase):
    def test_control_characters_fail_before_book_settlement(self):
        world, _, tree_id = bootstrap(437)
        session = SingleEngineSession(world, tree_id)
        before = session.audit()
        mass = dict(session.book.mass)
        energy = dict(session.book.energy)
        receipts = dict(session.book.request_receipts)
        for source, revision in (
            ('bad\nsource', '1'), ('source', 'bad\rrevision'),
            ('bad\tsource', '1'), ('source', 'bad\x00revision'),
            ('bad\x7fsource', '1'),
        ):
            with self.subTest(source=source, revision=revision):
                with self.assertRaisesRegex(ValueError, 'control characters'):
                    session.harvest('F001', source, revision, 'forest', 'plant', .01, .001)
                self.assertEqual(session.book.mass, mass)
                self.assertEqual(session.book.energy, energy)
                self.assertEqual(session.book.request_receipts, receipts)
                self.assertEqual(session.book.seq, before.book_sequence)
                self.assertEqual(world.tick, before.tick)
        after = session.audit()
        self.assertEqual(after.founder_count, 100)
        self.assertLess(abs(after.book_mass_error), 1e-6)
        self.assertLess(abs(after.book_energy_error), 1e-6)

    def test_ordinary_legacy_identity_remains_idempotent(self):
        world, _, tree_id = bootstrap(437)
        session = SingleEngineSession(world, tree_id)
        first = session.harvest('F001', 'legacy-source', 'r1', 'forest', 'plant', .01, .001)
        seq = session.book.seq
        again = session.harvest('F001', 'legacy-source', 'r1', 'forest', 'plant', .01, .001)
        self.assertEqual(first, again)
        self.assertEqual(seq, session.book.seq)
        session.audit()
