"""G1 adversarial exact-operation replay tests for the authoritative Book."""
import unittest
from founders_civ.core.ledger import Book


class G1ExactReplayTests(unittest.TestCase):
    def setUp(self):
        self.book = Book()
        self.book.seed_mass("plant:tree", 2.0)
        self.book.seed_energy("river_pool", 2.0)
        self.book.freeze()

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

    def test_fully_funded_death_transform_has_no_ulp_overdraw(self):
        book = Book()
        book.seed_mass("body:grazer", 1.65)
        book.seed_energy("embodied:grazer", 2.64)
        book.freeze()
        book.transform(
            [("body:grazer", "carcass:patch", 1.65)],
            "embodied:grazer", 2.64,
            energy_outputs=[
                ("embodied:grazer", "carrionchem:patch", 2.64 * .60),
                ("embodied:grazer", "heat:world", 2.64 * .30),
            ],
            operation_id="death:grazer",
        )
        self.assertEqual(book.energy["embodied:grazer"], 0.0)
        self.assertEqual(book.mass["body:grazer"], 0.0)
        self.assertEqual(book.seq, 1)
        book.audit()

    def test_death_transform_preserves_independent_food_chemical_transfer(self):
        book = Book()
        book.seed_mass("body:grazer", 1.65)
        book.seed_energy("embodied:grazer", 2.64)
        book.seed_energy("foodchem:grazer", .4)
        book.freeze()
        book.transform(
            [("body:grazer", "carcass:patch", 1.65)],
            "embodied:grazer", 2.64,
            energy_outputs=[
                ("foodchem:grazer", "carrionchem:patch", .4),
                ("embodied:grazer", "carrionchem:patch", 2.64 * .60),
                ("embodied:grazer", "heat:world", 2.64 * .30),
            ],
            operation_id="death:with_food",
        )
        self.assertEqual(book.energy["foodchem:grazer"], 0.0)
        self.assertEqual(book.energy["embodied:grazer"], 0.0)
        book.audit()

    def test_book_audits_energy_only_conservation_without_mass_seed(self):
        book = Book()
        book.seed_energy("founder:F1", .5)
        book.freeze()
        book.move(energy=[("founder:F1", "reserve:R1", .3)],
                  operation_id="energy:only")
        audit = book.audit()
        self.assertEqual(audit["mass_total"], 0.0)
        self.assertEqual(audit["energy_total"], .5)

    def test_photosynthesis_rejects_one_ulp_overspend_and_accepts_capped_work(self):
        sun = 1.7620248969090804
        # In the real ecology (sun / 3) * 3 exceeds the source by one ULP.
        inflated_work = (sun / 3.0) * 3.0
        self.assertGreater(inflated_work, sun)
        book = Book()
        book.seed_mass("soil:patch", 10.0)
        book.seed_energy("sun:patch", sun)
        book.freeze()
        with self.assertRaisesRegex(ValueError, "energy overdraw"):
            book.transform([("soil:patch", "plant:patch", sun / 3.0)],
                           "sun:patch", inflated_work,
                           [("sun:patch", "chem:patch", inflated_work * .74),
                            ("sun:patch", "heat:world", inflated_work * .16)])
        self.assertEqual(book.seq, 0)
        actual_work = min(sun, inflated_work)
        book.transform([("soil:patch", "plant:patch", sun / 3.0)],
                       "sun:patch", actual_work,
                       [("sun:patch", "chem:patch", actual_work * .74),
                        ("sun:patch", "heat:world", actual_work * .16)])
        self.assertEqual(book.seq, 1)
        self.assertEqual(book.energy["sun:patch"], 0.0)
        book.audit()

    def test_legacy_founder_work_rejects_roundoff_shortfall_before_book(self):
        # Reproduces the 180-day matched-seed failure at F032:
        # 0.08499999999999786 must not pay a 0.085 exploration cost.
        from types import SimpleNamespace
        from founders_civ.experimental.social_agents import SocialSimulation
        book=Book()
        book.seed_energy('founder:F032',0.08499999999999786)
        book.freeze()
        sim=SimpleNamespace(book=book,
                            _energy=lambda actor:book.energy[f'founder:{actor}'])
        before=(dict(book.energy),book.seq)
        self.assertIs(SocialSimulation._pay(sim,'F032','explore'),False)
        self.assertEqual(before,(dict(book.energy),book.seq))
        book.audit()

    def test_failed_transfer_does_not_claim_operation_identity(self):
        with self.assertRaisesRegex(ValueError, "material overdraw"):
            self.book.move(material=[("plant:tree", "plant:founder", 3.0)],
                           operation_id="g1:retry")
        self.assertNotIn("g1:retry", self.book.operations)
        self.book.move(material=[("plant:tree", "plant:founder", 1.0)],
                       operation_id="g1:retry")
        self.assertEqual(self.book.seq, 1)
        self.book.audit()


if __name__ == "__main__":
    unittest.main()
