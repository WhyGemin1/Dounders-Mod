"""C010 regression: digestion must consume actual Book chemical fuel and replay exactly."""
import pytest
from founders_civ.core.living_assets import TreeResourceOps
from founders_civ.core.ledger import Book

class Founders:
    people={'F1':object()}
class Sim:
    def __init__(self):self.book=Book();self.founders=Founders()
class Tree:
    def __init__(self):self.id='T1';self.sim=Sim();self.resources=TreeResourceOps(self)

def prepared(founder_fuel,body_fuel=0,number=1):
    tree=Tree();b=tree.sim.book
    for n in range(number):
        b.seed_mass(f'gut:founder:F1:lot:L{n}',.08)
        b.seed_energy(f'gut_energy:founder:F1:lot:L{n}',.02)
    b.seed_energy('founder:F1',founder_fuel)
    b.seed_energy('body_chemical:founder:F1',body_fuel)
    b.freeze()
    for n in range(number):b.operations[f'food:ingest:L{n}:F1']=(None,None)
    return tree

def test_body_fuel_can_fund_digestion_without_minting():
    tree=prepared(0,.002);b=tree.sim.book
    tree.resources.digest_food('L0','F1')
    assert b.energy['body_chemical:founder:F1']==pytest.approx(.002-.001+.015)
    assert b.energy['body_heat:founder:F1']==pytest.approx(.0059)
    assert b.audit()['energy_error']==pytest.approx(0)

def test_replay_keeps_original_fuel_source_after_balance_changes():
    tree=prepared(.001,.002);b=tree.sim.book
    first=tree.resources.digest_food('L0','F1')
    before=b.transactions
    assert tree.resources.digest_food('L0','F1')==first
    assert b.transactions==before

def test_second_meal_uses_energy_assimilated_from_first():
    tree=prepared(.001,0,number=2);b=tree.sim.book
    tree.resources.digest_food('L0','F1')
    tree.resources.digest_food('L1','F1')
    assert b.energy['body_chemical:founder:F1']==pytest.approx(.029)
    assert b.mass['assimilated:founder:F1']==pytest.approx(.10)
    assert b.audit()['energy_error']==pytest.approx(0)

def test_unfunded_digestion_rejects_without_mutating_book():
    tree=prepared(0,0);b=tree.sim.book
    before=(b.transactions,dict(b.mass),dict(b.energy))
    with pytest.raises(ValueError,match='insufficient existing metabolic fuel'):
        tree.resources.digest_food('L0','F1')
    assert (b.transactions,dict(b.mass),dict(b.energy))==before
