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


    def test_batch_identical_replay_remains_read_only(self):
        result = self.boundary.inspect_batch([self.claim, self.claim])
        self.assertEqual(len(result), 2)
        self.assertTrue(all(not x['book_settlement_allowed'] and
                            not x['ack_allowed'] for x in result))

    def test_batch_rejects_changed_request_identity_or_amount(self):
        for field, value in [('object_id', 'other-object'),
                             ('object_revision', 'r2'),
                             ('quantity', 2.0),
                             ('resource_unit', 'other-unit'),
                             ('ack_token', 'other-ack')]:
            with self.subTest(field=field), self.assertRaisesRegex(
                    ValueError, 'conflicting native request replay'):
                self.boundary.inspect_batch([
                    self.claim, replace(self.claim, **{field: value})])

    def test_batch_rejects_ack_token_collision(self):
        with self.assertRaisesRegex(ValueError, 'ACK token reused'):
            self.boundary.inspect_batch([
                self.claim, replace(self.claim, request_id='request-2')])

    def test_batch_invalid_claim_rejected_before_observation(self):
        with self.assertRaises(ValueError):
            self.boundary.inspect_batch([
                self.claim, replace(self.claim, quantity=float('nan'))])
        with self.assertRaises(TypeError):
            self.boundary.inspect_batch(iter((self.claim,)))


    def test_reject_noncanonical_native_identifiers(self):
        # Do not treat visually equivalent or control-bearing IDs as a
        # trustworthy source for cross-batch replay or external ACK.
        for field, value in (
            ('request_id', ' request-1'),
            ('request_id', 'request-1 '),
            ('request_id', 'request-1\n'),
            ('request_id', 'request-1\u200b'),
            ('request_id', 'request-' + 'x' * 257),
            ('world_id', 'world\x00one'),
            ('object_id', 'object-\u0065\u0301'),
            ('resource_unit', 'kg\t'),
            ('ack_token', 'ack-1\r'),
        ):
            with self.subTest(field=field, value=repr(value)):
                with self.assertRaisesRegex(ValueError, 'noncanonical'):
                    self.boundary.inspect(replace(self.claim, **{field: value}))

    def test_noncanonical_history_rejected_before_replay_result(self):
        invalid = replace(self.claim, request_id='request-1\u200b')
        with self.assertRaisesRegex(ValueError, 'noncanonical'):
            self.boundary.inspect_against_history([invalid], [self.claim])
        with self.assertRaisesRegex(ValueError, 'noncanonical'):
            self.boundary.inspect_against_history([self.claim], [invalid])

    def test_cross_batch_replay_is_read_only(self):
        observations = self.boundary.inspect_against_history(
            [self.claim], [self.claim])
        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0]['status'], 'OBSERVED_UNVERIFIED')
        self.assertFalse(observations[0]['ack_allowed'])
        self.assertFalse(observations[0]['book_settlement_allowed'])

    def test_cross_batch_changed_quantity_and_identity_rejected(self):
        for field, value in [('quantity', 3.0),
                             ('object_revision', 'r2'),
                             ('resource_unit', 'another-unit'),
                             ('game_version', 'other-version')]:
            with self.subTest(field=field), self.assertRaisesRegex(
                    ValueError, 'conflicting native request replay'):
                self.boundary.inspect_against_history(
                    [self.claim], [replace(self.claim, **{field: value})])

    def test_cross_batch_ack_collision_rejected(self):
        with self.assertRaisesRegex(ValueError, 'ACK token reused'):
            self.boundary.inspect_against_history(
                [self.claim], [replace(self.claim, request_id='request-2')])

    def test_missing_history_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'complete trusted'):
            self.boundary.inspect_against_history(None, [self.claim])
        with self.assertRaises(TypeError):
            self.boundary.inspect_against_history(iter([self.claim]), [self.claim])

if __name__ == '__main__':
    unittest.main()
