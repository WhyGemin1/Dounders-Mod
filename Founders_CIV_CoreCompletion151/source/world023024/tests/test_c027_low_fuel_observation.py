"""C027 regression: observation requires funded fuel, not .19 work threshold."""
import unittest
from run_world_tree_pilot import bootstrap

class LowFuelObservation(unittest.TestCase):
    def test_affordable_observation(self):
        sim, realm, tid = bootstrap(seed=820)
        tree = sim.world_trees.worlds[tid]
        founder = tree.owner
        sim.founders.people[founder].location = 'riverbank'
        account = f'founder:{founder}'
        old = sim.book.energy[account]
        self.assertGreater(old, .19)
        sim.book.move(energy=[(account, 'environment:heat', old-.05)])
        choice = next(p for p in sim._proposals(founder, [])
                      if p[1]=='tree_observe' and p[3]==tid)
        before = sim.book.energy[account]
        sim._do(founder, choice, [], None, 'test:c027')
        self.assertAlmostEqual(sim.book.energy[account], before-.025)
        self.assertLess(abs(sim.book.audit()['energy_error']), 1e-5)

    def test_insufficient_fuel(self):
        sim, realm, tid = bootstrap(seed=820)
        founder = sim.world_trees.worlds[tid].owner
        sim.founders.people[founder].location = 'riverbank'
        account = f'founder:{founder}'
        sim.book.move(energy=[(account, 'environment:heat',
                               sim.book.energy[account]-.01)])
        self.assertFalse(any(p[1]=='tree_observe'
                             for p in sim._proposals(founder, [])))
