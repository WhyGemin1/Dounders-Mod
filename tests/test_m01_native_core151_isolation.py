"""M01 native observation isolation against the REAL Core151 IntegratedWorld.

The boundary must never transact the one Book, advance the one clock,
change Founder identities, or issue native acknowledgments. Seed 400 pilot.
"""
import unittest
from dataclasses import replace

from run_world_tree_pilot import bootstrap
from founders_engine.authority import SingleEngineSession
from founders_engine.native_claim_boundary import NativeClaim, NativeClaimBoundary


class RealCore151NativeIsolationTests(unittest.TestCase):
    def setUp(self):
        world, _, tree_id = bootstrap(400)
        self.session = SingleEngineSession(world, tree_id)
        self.boundary = NativeClaimBoundary()
        self.claim = NativeClaim(
            'worldbox-m01-unverified', 'unknown-version', 'native-world-1',
            'native-object-1', 'revision-1', 'request-1',
            'plant', 'unknown-native-unit', 1.0, 'ack-1')

    def snapshot(self):
        s = self.session
        b = s.book
        audit = b.audit()
        return (id(s.world.book), id(s.world.founders.book),
                s.world.tick, s.world.ecology.day, b.seq,
                dict(b.mass), dict(b.energy),
                dict(b.request_receipts),
                tuple(sorted(s.world.founders.people)),
                audit['mass_error'], audit['energy_error'])

    def test_valid_observation_never_touches_real_world(self):
        before = self.snapshot()
        observations = self.boundary.inspect_against_history(
            [self.claim], [self.claim])
        self.assertEqual(len(observations), 1)
        self.assertFalse(observations[0]['book_settlement_allowed'])
        self.assertFalse(observations[0]['ack_allowed'])
        self.assertEqual(before, self.snapshot())
        self.assertEqual(len(self.session.world.founders.people), 100)

    def test_conflict_never_touches_real_world(self):
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'conflicting native request'):
            self.boundary.inspect_against_history(
                [self.claim], [replace(self.claim, quantity=2.0)])
        self.assertEqual(before, self.snapshot())

    def test_settle_and_ack_are_disabled_even_with_core151_session(self):
        before = self.snapshot()
        with self.assertRaises(PermissionError):
            self.boundary.settle(self.claim, self.session)
        with self.assertRaises(PermissionError):
            self.boundary.acknowledge(self.claim, self.session)
        self.assertEqual(before, self.snapshot())


if __name__ == '__main__':
    unittest.main()
