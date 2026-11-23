"""C190: Founder proposals require the paired Book-owned chemical charge.

A lot with its biomass but without chemical energy is not a viable meal.
No second inventory, energy creation, or native WorldBox write is introduced.
"""
from test_c015_founder_nutrition import prepared, harvest
from founders_civ.core.founder_nutrition import propose_nutrition, perform_nutrition


def test_no_ingest_proposal_for_mass_without_paired_charge():
    sim, tree, founder, lot = prepared()
    harvest(sim, tree, founder, lot)
    account = f'food_energy:lot:{lot}:founder:{founder}'
    amount = sim.book.energy[account]
    sim.book.move(energy=[(account, 'environment:heat', amount)])
    before = sim.book.seq
    assert not any(p[1] == 'food_ingest' for p in propose_nutrition(sim, founder))
    assert sim.book.seq == before
    assert abs(sim.book.audit()['energy_error']) < 1e-5


def test_no_digest_proposal_for_gut_mass_without_paired_charge():
    sim, tree, founder, lot = prepared()
    harvest(sim, tree, founder, lot)
    perform_nutrition(sim, founder, 'food_ingest', (tree.id, lot))
    account = f'gut_energy:founder:{founder}:lot:{lot}'
    amount = sim.book.energy[account]
    sim.book.move(energy=[(account, 'environment:heat', amount)])
    before = sim.book.seq
    assert not any(p[1] == 'food_digest' for p in propose_nutrition(sim, founder))
    assert sim.book.seq == before
    assert abs(sim.book.audit()['energy_error']) < 1e-5
