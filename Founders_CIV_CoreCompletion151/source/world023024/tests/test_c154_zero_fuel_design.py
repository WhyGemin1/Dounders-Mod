"""C154: voluntary design is a free decision; construction still requires funding."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from founders_civ.core.founder_tree_agency import propose_self_trees


class FreeDesignTests(unittest.TestCase):
    def test_zero_fuel_founder_can_propose_but_not_create_resources(self):
        founder = "F-001"
        person = SimpleNamespace(alive=True)
        realm = {"id": "realm-1", "kind": "realm", "status": "stable", "owner": "other"}
        sim = SimpleNamespace(
            founder_tree_independence_enabled=True,
            founders=SimpleNamespace(people={founder: person}),
            seeds=SimpleNamespace(plants={"realm-1": realm}, blueprints={}),
            book=SimpleNamespace(energy={}, mass={}, operations={}),
        )
        with patch("founders_civ.core.founder_tree_agency._own_fruit", return_value=iter([("tree-1", "lot-1")])):
            proposals = propose_self_trees(sim, founder, [])
        self.assertEqual(proposals, [(4.35, "seed_design", None, ("world", "realm-1"))])
        self.assertEqual(sim.book.operations, {})
        self.assertEqual(sim.book.energy, {})

    def test_without_fruit_no_design_even_with_free_decision(self):
        founder = "F-001"
        sim = SimpleNamespace(
            founder_tree_independence_enabled=True,
            founders=SimpleNamespace(people={founder: SimpleNamespace(alive=True)}),
            seeds=SimpleNamespace(plants={"realm-1": {"id": "realm-1", "kind": "realm", "status": "stable"}}, blueprints={}),
            book=SimpleNamespace(energy={}, operations={}),
        )
        with patch("founders_civ.core.founder_tree_agency._own_fruit", return_value=iter(())):
            self.assertEqual(propose_self_trees(sim, founder, []), [])


if __name__ == "__main__":
    unittest.main()
