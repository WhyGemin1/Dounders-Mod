"""Book-funded synthetic World Tree harvest. NOT a native WorldBox connector.

Only the Core151 Book and clock are authoritative. The request identifier is
local, not a verified WorldBox object ID. Checkpoint replay still needs a gate.
"""
from dataclasses import dataclass
from math import isfinite

@dataclass(frozen=True)
class HarvestReceipt:
    request_id: str
    transaction_seq: int
    founder_id: str
    tree_id: str
    habitat: str
    material: str
    quantity: float
    chemical_energy: float

class WorldBoxGatewayM01:
    ALLOWED = frozenset(('plant', 'detritus'))

    def __init__(self, tree):
        if tree.book is not tree.sim.book:
            raise ValueError('World Tree has foreign Book')
        self.tree, self.sim, self.book = tree, tree.sim, tree.book

    def founder_harvest(self, founder_id, source_id, revision, habitat,
                        material, quantity, chemical_energy=0.0):
        if self.tree.book is not self.book or self.sim.book is not self.book:
            raise ValueError('Book authority changed')
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError('request source_id required')
        if not isinstance(revision, str) or not revision.strip():
            raise ValueError('request revision required')
        # The durable receipt key uses ':' as a field delimiter. Reject ambiguous
        # components rather than allowing two different source/revision pairs
        # to alias the same Book transaction across checkpoint restarts.
        if ':' in source_id or ':' in revision:
            raise ValueError('request identity components cannot contain colon')
        request_id = f'm01:{self.tree.id}:{source_id}:{revision}'
        founder = self.sim.founders.people.get(founder_id)
        if founder is None or not founder.alive:
            raise ValueError('active Founder required')
        if self.tree.state == 'archived':
            raise ValueError('collapsed World Tree cannot be harvested')
        if habitat not in self.tree.habitats or material not in self.ALLOWED:
            raise ValueError('unsupported harvest habitat/material')
        for value in (quantity, chemical_energy):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
                raise ValueError('finite numeric amount required')
        if quantity <= 0 or chemical_energy < 0:
            raise ValueError('invalid harvest amount')
        msrc = self.tree.acct(material, habitat)
        mdst = f'{material}:founder:{founder_id}'
        energy_legs = ()
        if chemical_energy:
            energy_legs = ((self.tree.acct('chem', habitat),
                            f'chem:founder:{founder_id}', chemical_energy),)
        tx, first_settlement = self.book.move_once(
            request_id, material=((msrc, mdst, quantity),), energy=energy_legs)
        if first_settlement:
            self.sim.log('m01_harvest', founder_id, txn=tx, request_id=request_id,
                         tree_id=self.tree.id, habitat=habitat, material=material,
                         quantity=quantity, chemical_energy=chemical_energy)
        return HarvestReceipt(request_id, tx.seq, founder_id, self.tree.id,
                              habitat, material, quantity, chemical_energy)
