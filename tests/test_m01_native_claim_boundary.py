"""Fail-closed native claim boundary, without constructing a second engine."""
import unittest
from dataclasses import replace
from founders_engine.native_claim_boundary import NativeClaim, NativeClaimBoundary

class NativeBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.boundary = NativeClaimBoundary()
        self.claim = NativeClaim('worldbox-m01-unverified','unknown-version',
            'world-1','native-object-1','revision-1','request-1',
            'plant','native-unknown-unit',1.0,'ack-1')

    def test_observation_cannot_settle_or_ack(self):
        result = self.boundary.inspect(self.claim)
        self.assertEqual(result['status'], 'OBSERVED_UNVERIFIED')
        self.assertFalse(result['native_writes_allowed'])
        self.assertFalse(result['book_settlement_allowed'])
        self.assertFalse(result['ack_allowed'])
        with self.assertRaises(PermissionError):
            self.boundary.settle(self.claim)
        with self.assertRaises(PermissionError):
            self.boundary.acknowledge(self.claim)

    def test_missing_identity_unit_or_version_is_rejected(self):
        for name in ('game_version','world_id','object_id','object_revision',
                     'request_id','resource_unit','ack_token'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.boundary.inspect(replace(self.claim, **{name:''}))

    def test_bad_quantities_rejected(self):
        for value in (float('nan'), float('inf'), -1.0, 0.0, True, '1'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.boundary.inspect(replace(self.claim, quantity=value))

if __name__ == '__main__':
    unittest.main()
