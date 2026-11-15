"""C009 digestion contract against the C013 per-lot Book implementation.

A concrete identified food lot, not a shared gut pool, is the digestible asset.
"""
import pytest
from founders_civ.core.living_assets import TreeResourceOps
from founders_civ.core.ledger import Book


class Founders:
    people = {'F1': object()}


class Sim:
    def __init__(self):
        self.book = Book()
        self.founders = Founders()


class Tree:
    def __init__(self):
        self.id = 'T1'
        self.sim = Sim()
        self.resources = TreeResourceOps(self)


def prepared():
    tree = Tree()
    b = tree.sim.book
    b.seed_mass('gut:founder:F1:lot:L1', .08)
    b.seed_energy('gut_energy:founder:F1:lot:L1', .02)
    b.seed_energy('founder:F1', .001)
    b.freeze()
    b.operations['food:ingest:L1:F1'] = (None, None)
    return tree


def test_no_uningested_lot_can_digest():
    tree = prepared()
    before = tree.sim.book.transactions
    with pytest.raises(ValueError, match='not ingested'):
        tree.resources.digest_food('L2', 'F1')
    assert tree.sim.book.transactions == before


def test_digest_book_conservation_and_replay():
    tree = prepared()
    b = tree.sim.book
    txn = tree.resources.digest_food('L1', 'F1')
    assert b.mass['assimilated:founder:F1'] == pytest.approx(.05)
    assert b.mass['waste:founder:F1'] == pytest.approx(.03)
    assert b.energy['body_chemical:founder:F1'] == pytest.approx(.015)
    assert b.energy['body_heat:founder:F1'] == pytest.approx(.0059)
    assert b.audit()['energy_error'] == pytest.approx(0)
    count = b.transactions
    assert tree.resources.digest_food('L1', 'F1') == txn
    assert b.transactions == count


def test_digest_requires_real_metabolic_work():
    tree = prepared()
    tree.sim.book.move(energy=[('founder:F1', 'environment:heat', .001)])
    with pytest.raises((ValueError, AssertionError)):
        tree.resources.digest_food('L1', 'F1')
