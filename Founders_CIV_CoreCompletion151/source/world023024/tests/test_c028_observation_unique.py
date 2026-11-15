import unittest
from run_world_tree_pilot import bootstrap

class ObservationUnique(unittest.TestCase):
    def test_no_duplicate_observation_at_intermediate_fuel(self):
        sim, realm, tid = bootstrap(seed=820)
        founder = sim.world_trees.worlds[tid].owner
        sim.founders.people[founder].location = 'riverbank'
        account = f'founder:{founder}'
        sim.book.move(energy=[(account, 'environment:heat', sim.book.energy[account] - .15)])
        props = sim._proposals(founder, [])
        matches = [p for p in props if p[1] == 'tree_observe' and p[3] == tid]
        self.assertEqual(len(matches), 1)
        self.assertLess(abs(sim.book.audit()['energy_error']), 1e-5)

if __name__ == '__main__':
    unittest.main()
