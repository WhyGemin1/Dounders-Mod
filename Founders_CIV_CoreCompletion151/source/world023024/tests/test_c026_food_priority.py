"""C026: depleted Founders prioritize previously observed food over seed fruit."""
import unittest
from run_world_tree_pilot import bootstrap
from founders_civ.core.founder_harvesting import observed_lots, propose_harvest

class FoodPriority(unittest.TestCase):
    def test_low_fuel_food_ranks_above_fruit_without_book_transfer(self):
        sim, _, tid = bootstrap(seed=821)
        tree = sim.world_trees.worlds[tid]
        tree.enable_provisioning()
        for _ in range(25):
            sim.step()
        actor = 'F001'
        sim.founder_harvest_enabled = True
        sim.founders.people[actor].location = 'riverbank'
        tree.observe(actor)
        tree.observations[actor]['known_lots'] = observed_lots(tree)
        choices = propose_harvest(sim, actor)
        food = [p for p in choices if p[3][2] == 'food']
        fruit = [p for p in choices if p[3][2] == 'fruit']
        self.assertTrue(food and fruit, 'fixture must contain both edible food and mature fruit')
        original = max(p[0] for p in food)
        fuel = sim.book.energy[f'founder:{actor}']
        if fuel:
            sim.book.move(energy=[(f'founder:{actor}', 'environment:heat', fuel)])
        new = propose_harvest(sim, actor)
        food2 = [p for p in new if p[3][2] == 'food']
        fruit2 = [p for p in new if p[3][2] == 'fruit']
        self.assertGreater(max(p[0] for p in food2), max(p[0] for p in fruit2))
        self.assertAlmostEqual(max(p[0] for p in food2), original + 1.0)
        self.assertLess(abs(sim.book.audit()['energy_error']), 1e-4)
        self.assertLess(abs(sim.book.audit()['mass_error']), 1e-5)
