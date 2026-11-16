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
