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
