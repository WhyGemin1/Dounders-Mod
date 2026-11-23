from integrated_02179 import Unified279

def test_opt_in_budget_conserves_energy():
    sim=Unified279(seed=9711,energy_budget=True)
    b=sim.bridge
    a=next(x for x in b.actors.values() if x.alive and x.species=='ridge_hound')
    key=b.physical.reserve(a)
    b.book.energy[key]=.002
    before=b.book.energy[key]
    b._metabolize(a)
    assert 0 < before-b.book.energy[key] < .001*(.5+.5*__import__('species_life_02115').PROFILES[a.species].metabolism/.1)

def test_opt_out_preserves_original_policy():
    sim=Unified279(seed=9711,energy_budget=False)
    assert sim.energy_budget is False
