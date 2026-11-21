"""Smoke gate for the one authoritative Core151 IntegratedWorld.
Run: PYTHONPATH=src python -m unittest -v tests.test_core151_smoke
This is headless and does not establish WorldBox in-game compatibility.
"""
import unittest
from run_world_tree_pilot import bootstrap
from founders_civ.core.ledger import Book

class Core151Smoke(unittest.TestCase):
    def test_book_founder_clock(self):
        sim, _, tree_id = bootstrap(400)
        self.assertIsInstance(sim.book, Book)
        self.assertIs(sim.world_trees.worlds[tree_id].book, sim.book)
        self.assertIs(sim.founders.book, sim.book)
        self.assertEqual(len(sim.founders.people), 100)
        before = sim.tick
        sim.step()
        self.assertEqual(sim.tick, before + 1)
        audit = sim.book.audit()
        self.assertLess(abs(audit['mass_error']), 1e-6)
        self.assertLess(abs(audit['energy_error']), 1e-6)

if __name__ == '__main__':
    unittest.main()
