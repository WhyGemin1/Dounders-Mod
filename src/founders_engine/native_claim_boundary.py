"""M01 external claim boundary: strict read-only validation, never native settlement.

This is an admission gate for a *future* native WorldBox adapter, not a
WorldBox plugin. A validated claim is NOT permission to debit Core151 Book.
Native version, identity and unit mappings must be independently verified.
"""
from dataclasses import dataclass
from math import isfinite

@dataclass(frozen=True)
class NativeClaim:
    protocol: str
    game_version: str
    world_id: str
    object_id: str
    object_revision: str
    request_id: str
    resource_kind: str
    resource_unit: str
    quantity: float
    ack_token: str

class NativeClaimBoundary:
    """Fail-closed observational validation. No Book, tick, or game writes."""

    def __init__(self, verified_contract=None):
        # A contract is a separate, reviewed native integration artifact.
        # No such contract is bundled or inferred from synthetic M01 units.
        self._verified_contract = verified_contract

    def inspect(self, claim):
        if not isinstance(claim, NativeClaim):
            raise TypeError('typed native claim required')
        fields = (claim.protocol, claim.game_version, claim.world_id,
                  claim.object_id, claim.object_revision, claim.request_id,
                  claim.resource_kind, claim.resource_unit, claim.ack_token)
        if any(not isinstance(x, str) or not x.strip() for x in fields):
            raise ValueError('all native identity/version/unit/ACK fields required')
        if isinstance(claim.quantity, bool) or not isinstance(claim.quantity, (int, float)):
            raise ValueError('numeric quantity required')
        if not isfinite(claim.quantity) or claim.quantity <= 0:
            raise ValueError('finite positive quantity required')
        # Never interpret an unverified native unit as a synthetic Book unit.
        return {'status': 'OBSERVED_UNVERIFIED', 'request_id': claim.request_id,
                'native_writes_allowed': False, 'book_settlement_allowed': False,
                'ack_allowed': False}

    def settle(self, claim, *args, **kwargs):
        self.inspect(claim)
        raise PermissionError('native WorldBox settlement disabled: identity, units, version and ACK unverified')

    def acknowledge(self, claim, *args, **kwargs):
        self.inspect(claim)
        raise PermissionError('native WorldBox ACK disabled: no verified exactly-once protocol')

    def inspect_batch(self, claims):
        """Validate one read-only observation batch and reject ambiguous replays.

        This is deliberately stateless: the Core151 Book remains the only
        transaction authority. Cross-batch replay safety still requires a
        verified native transaction protocol and durable checkpoint receipts.
        """
        if not isinstance(claims, (tuple, list)):
            raise TypeError('ordered claim batch required')
        by_request = {}
        by_ack = {}
        observations = []
        for claim in claims:
            observed = self.inspect(claim)
            # A request identifier is not permission to settle. It must not
            # be reused for a different native object, revision or quantity.
            prior = by_request.get(claim.request_id)
            if prior is not None and prior != claim:
                raise ValueError('conflicting native request replay')
            prior_ack = by_ack.get(claim.ack_token)
            if prior_ack is not None and prior_ack != claim.request_id:
                raise ValueError('native ACK token reused across requests')
            by_request[claim.request_id] = claim
            by_ack[claim.ack_token] = claim.request_id
            observations.append(observed)
        return tuple(observations)
