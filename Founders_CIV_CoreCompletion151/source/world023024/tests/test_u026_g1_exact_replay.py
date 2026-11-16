"""G1 adversarial exact-operation replay tests for the authoritative Book."""
import unittest
from founders_civ.core.ledger import Book


class G1ExactReplayTests(unittest.TestCase):
    def setUp(self):
        self.book = Book()
        self.book.seed_mass("plant:tree", 2.0)
        self.book.seed_energy("river_pool", 2.0)
        self.book.freeze()

    def test_ieee_rounding_only_does_not_block_funded_physical_transfer(self):
        book = Book()
        book.seed_energy("embodied:funded", 2.64)
        book.freeze()
        # Several floating-point legs may overstate the debit by one ULP.
        book.move(energy=[("embodied:funded", "heat", 2.6400000000000006)])
        self.assertEqual(book.energy["embodied:funded"], 0.)
        self.assertLess(abs(book.audit()["energy_error"]), 1e-12)

    def test_real_tiny_overdraft_above_ulp_is_still_fail_closed(self):
        book = Book()
        book.seed_energy("embodied:funded", 2.64)
        book.freeze()
        before = (dict(book.energy), book.seq)
        with self.assertRaisesRegex(ValueError, "energy overdraw"):
            book.move(energy=[("embodied:funded", "heat", 2.640000000001)])
        self.assertEqual(before, (dict(book.energy), book.seq))
        book.audit()

    def test_exact_retry_returns_original_without_second_debit(self):
        tx = self.book.move(material=[("plant:tree", "plant:founder", 0.5)],
                            operation_id="g1:harvest:1")
        self.assertIs(self.book.move(material=[("plant:tree", "plant:founder", 0.5)],
                                     operation_id="g1:harvest:1"), tx)
        self.assertEqual(self.book.seq, 1)
        self.assertEqual(self.book.mass["plant:tree"], 1.5)
        self.book.audit()

    def test_subpicounit_conflicting_retry_is_rejected_atomically(self):
        self.book.move(material=[("plant:tree", "plant:founder", 0.5)],
                       operation_id="g1:harvest:1")
        before = (dict(self.book.mass), dict(self.book.energy),
                  self.book.seq, len(self.book.operations))
        with self.assertRaisesRegex(ValueError, "conflicting operation ID"):
            self.book.move(material=[("plant:tree", "plant:founder", 0.5000000000001)],
                           operation_id="g1:harvest:1")
        self.assertEqual(before, (dict(self.book.mass), dict(self.book.energy),
                                  self.book.seq, len(self.book.operations)))
        self.book.audit()

    def test_conflicting_creation_charge_retry_rejected(self):
        self.book.reserve_creation_charge(0.5, "g1:reserve:1")
        before = (dict(self.book.energy), self.book.seq)
        with self.assertRaisesRegex(ValueError, "conflicting operation ID"):
            self.book.reserve_creation_charge(0.5000000000001, "g1:reserve:1")
        self.assertEqual(before, (dict(self.book.energy), self.book.seq))
        self.book.audit()

    def test_sub_epsilon_empty_material_source_cannot_mint_stock(self):
        before = (dict(self.book.mass), self.book.seq)
        with self.assertRaisesRegex(ValueError, "material overdraw"):
            self.book.move(material=[("plant:empty", "plant:founder", 5e-8)],
                           operation_id="g1:tiny:mass")
        self.assertEqual(before, (dict(self.book.mass), self.book.seq))
        self.assertNotIn("g1:tiny:mass", self.book.operations)
        self.book.audit()

    def test_sub_epsilon_empty_energy_source_cannot_mint_fuel(self):
        before = (dict(self.book.energy), self.book.seq)
        with self.assertRaisesRegex(ValueError, "energy overdraw"):
            self.book.move(energy=[("body_chemical:empty", "body_chemical:founder", 5e-8)],
                           operation_id="g1:tiny:energy")
        self.assertEqual(before, (dict(self.book.energy), self.book.seq))
        self.assertNotIn("g1:tiny:energy", self.book.operations)
        self.book.audit()

    def test_sub_epsilon_river_ce_overdraw_is_rejected(self):
        self.book.reserve_creation_charge(2.0, "g1:reserve:all")
        before = (dict(self.book.energy), self.book.seq)
        with self.assertRaisesRegex(ValueError, "energy overdraw"):
            self.book.reserve_creation_charge(5e-8, "g1:reserve:extra")
        self.assertEqual(before, (dict(self.book.energy), self.book.seq))
        self.book.audit()

    def test_small_funded_transfer_remains_allowed(self):
        self.book.move(material=[("plant:tree", "plant:founder", 5e-8)],
                       operation_id="g1:tiny:funded")
        self.assertEqual(self.book.mass["plant:founder"], 5e-8)
        self.book.audit()

    def test_nonfinite_material_replay_rejected_without_mutation(self):
        self.book.move(material=[("plant:tree", "plant:founder", 0.5)],
                       operation_id="g1:nonfinite:material")
        before = (dict(self.book.mass), self.book.seq)
        for invalid in (float("nan"), float("inf"), float("-inf")):
            with self.assertRaisesRegex(ValueError, "invalid transfer quantity"):
                self.book.move(material=[("plant:tree", "plant:founder", invalid)],
                               operation_id="g1:nonfinite:material")
        self.assertEqual(before, (dict(self.book.mass), self.book.seq))
        self.book.audit()

    def test_nonfinite_ce_replay_rejected_without_mutation(self):
        self.book.reserve_creation_charge(0.5, "g1:nonfinite:ce")
        before = (dict(self.book.energy), self.book.seq)
        for invalid in (float("nan"), float("inf"), float("-inf")):
            with self.assertRaisesRegex(ValueError, "invalid transfer quantity"):
                self.book.reserve_creation_charge(invalid, "g1:nonfinite:ce")
        self.assertEqual(before, (dict(self.book.energy), self.book.seq))
        self.book.audit()

    def test_zero_or_negative_replay_amount_is_not_idempotent(self):
        self.book.move(material=[("plant:tree", "plant:founder", 0.5)],
                       operation_id="g1:nonpositive")
        before = (dict(self.book.mass), self.book.seq)
        for invalid in (0.0, -0.5):
            with self.assertRaisesRegex(ValueError, "invalid transfer quantity"):
                self.book.move(material=[("plant:tree", "plant:founder", invalid)],
                               operation_id="g1:nonpositive")
        self.assertEqual(before, (dict(self.book.mass), self.book.seq))
        self.book.audit()

    def test_failed_transfer_does_not_claim_operation_identity(self):
        with self.assertRaisesRegex(ValueError, "material overdraw"):
            self.book.move(material=[("plant:tree", "plant:founder", 3.0)],
                           operation_id="g1:retry")
        self.assertNotIn("g1:retry", self.book.operations)
        self.book.move(material=[("plant:tree", "plant:founder", 1.0)],
                       operation_id="g1:retry")
        self.assertEqual(self.book.seq, 1)
        self.book.audit()


class G1CompositeAtomicityTests(unittest.TestCase):
    """Failure injection: a failed *composite* must not spend Book resources."""

    def test_failed_fruit_growth_does_not_reserve_chemical_or_creation_charge(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        from founders_civ.core.autonomous_provisioning import TreeProvisioningPolicy

        book = Book()
        book.seed_mass("plant:T1:forest", 4.)
        book.seed_energy("sun:T1:forest", .2)
        book.seed_energy("river_pool", 2.)
        book.freeze()
        tree = SimpleNamespace(
            id="T1", age=12, state="active", book=book, residents={},
            sim=SimpleNamespace(seeds=SimpleNamespace(plants={"T1": {"status": "stable"}})),
            acct=lambda kind, biome: f"{kind}:T1:{biome}",
            grow_creation_fruit=Mock(side_effect=RuntimeError("injected fruit-growth failure"))
        )
        policy = TreeProvisioningPolicy(tree, minimum_plant=1.)
        before = (dict(book.mass), dict(book.energy), book.seq, dict(book.operations))
        with self.assertRaisesRegex(RuntimeError, "injected fruit-growth failure"):
            policy._allocate("fruit", "forest")
        self.assertEqual(before, (dict(book.mass), dict(book.energy),
                                  book.seq, dict(book.operations)))
        self.assertEqual(policy.lots, {})
        self.assertEqual(policy.events, [])
        book.audit()

    def test_failed_world_registration_after_real_build_rolls_back_book_and_construct(self):
        from types import SimpleNamespace
        from unittest.mock import Mock, patch
        from founders_civ.experimental.world_integration import SeedRegistry, SeedBlueprint, RULE_DEFAULTS
        from founders_civ.experimental.world_trees import WorldTree

        book = Book()
        book.seed_mass("soil:Solara:grassland", 10.)
        book.seed_energy("founder:F1", 3.)
        book.seed_energy("house", 20.)
        book.freeze()
        worlds = SimpleNamespace(worlds={}, add=Mock(side_effect=RuntimeError("injected Tree registration failure")))
        sim = SimpleNamespace(
            book=book, tick=3, world_trees=worlds,
            founders=SimpleNamespace(people={"F1": SimpleNamespace(alive=True)}))
        seeds = SeedRegistry(sim)
        seeds.plants["CRE-PARENT"] = {"id": "CRE-PARENT", "kind": "realm", "status": "stable"}
        blueprint = SeedBlueprint(
            id="SEED-00001", author="F1", kind="world", name="First World",
            parent_id="CRE-PARENT", rules=dict(RULE_DEFAULTS),
            created_tick=0, stage="validated")
        seeds.blueprints[blueprint.id] = blueprint
        prior = (dict(book.mass), dict(book.energy), book.seq, dict(book.operations))
        with patch.object(WorldTree, "preflight", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "injected Tree registration failure"):
                seeds.plant("F1", blueprint.id)
        self.assertEqual(prior, (dict(book.mass), dict(book.energy),
                                 book.seq, dict(book.operations)))
        self.assertEqual(set(seeds.plants), {"CRE-PARENT"})
        self.assertEqual(seeds.constructs.items, {})
        self.assertEqual(worlds.worlds, {})
        self.assertEqual(blueprint.stage, "validated")
        book.audit()

    def test_failed_construct_build_does_not_debit_founder_or_claim_creation(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        from founders_civ.experimental.world_integration import SeedRegistry, SeedBlueprint, RULE_DEFAULTS

        book = Book()
        book.seed_mass("soil:Solara:grassland", 10.)
        book.seed_energy("founder:F1", 3.)
        book.seed_energy("house", 20.)
        book.freeze()
        sim = SimpleNamespace(
            book=book, tick=3,
            founders=SimpleNamespace(people={"F1": SimpleNamespace(alive=True)}))
        seeds = SeedRegistry(sim)
        blueprint = SeedBlueprint(
            id="SEED-00001", author="F1", kind="realm", name="First Realm",
            parent_id=None, rules=dict(RULE_DEFAULTS), created_tick=0,
            x=30., y=30., stage="validated")
        seeds.blueprints[blueprint.id] = blueprint
        seeds.constructs.build = Mock(side_effect=RuntimeError("injected construct-build failure"))
        before = (dict(book.mass), dict(book.energy), book.seq, dict(book.operations))
        with self.assertRaisesRegex(RuntimeError, "injected construct-build failure"):
            seeds.plant("F1", blueprint.id)
        self.assertEqual(before, (dict(book.mass), dict(book.energy),
                                  book.seq, dict(book.operations)))
        self.assertEqual(seeds.plants, {})
        self.assertEqual(blueprint.stage, "validated")
        book.audit()


if __name__ == "__main__":
    unittest.main()
