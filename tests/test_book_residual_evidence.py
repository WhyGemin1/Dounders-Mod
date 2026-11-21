"""Numerical conservation evidence from the actual Core151 world, not a mock engine."""
import math
import unittest

from founders_engine.authority import SingleEngineSession
from run_world_tree_pilot import bootstrap


class BookResidualEvidenceTests(unittest.TestCase):
    def test_real_tick_reports_finite_conservation_residuals(self):
        world, _, tree_id = bootstrap(427)
        session = SingleEngineSession(world, tree_id)
        before = session.audit()
        self.assertEqual(before.founder_count, 100)
        self.assertIs(world.book, session.book)
        self.assertEqual(world.tick, before.tick)
        self.assertEqual(world.ecology.day, before.tick)
        self.assertLessEqual(abs(before.book_mass_error), 1e-6)
        self.assertLessEqual(abs(before.book_energy_error), 1e-6)

        session.step()
        after = session.audit()
        self.assertEqual(after.tick, before.tick + 1)
        self.assertEqual(world.ecology.day, after.tick)
        self.assertGreaterEqual(after.book_sequence, before.book_sequence)
        for residual in (after.book_mass_error, after.book_energy_error):
            self.assertTrue(math.isfinite(residual))
            self.assertLessEqual(abs(residual), 1e-6)

        print("CORE151_BOOK_RESIDUAL seed=427 "
              f"before_tick={before.tick} after_tick={after.tick} "
              f"before_seq={before.book_sequence} after_seq={after.book_sequence} "
              f"before_mass={before.book_mass_error:.17g} "
              f"before_energy={before.book_energy_error:.17g} "
              f"after_mass={after.book_mass_error:.17g} "
              f"after_energy={after.book_energy_error:.17g}")


if __name__ == "__main__":
    unittest.main()
