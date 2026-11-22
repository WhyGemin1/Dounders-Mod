"""G2 voluntary parent-Realm stewardship: Book funding, replay, and agency.

All tests operate on the real Core151 Book and the actual stewardship policy
with minimal actor/Realm fixtures; no simulated free energy is provided.
"""
import unittest
from types import SimpleNamespace

from founders_civ.core.ledger import Book
from founders_civ.core.founder_parent_stewardship import (
    dependent_parent_ids,
    inspect_parent,
    propose_parent_stewardship,
    tend_parent,
)


class G2ParentStewardshipTests(unittest.TestCase):
    def setUp(self):
        self.logs = []
        book = Book()
        book.seed_energy("founder:F1", 2.0)
        book.seed_energy("reserve:R1", 0.05)
        book.seed_energy("ce:river", 1.0)
        book.freeze()
        self.sim = SimpleNamespace(
            tick=3,
            book=book,
            founder_parent_stewardship_enabled=True,
            founders=SimpleNamespace(people={
                "F1": SimpleNamespace(alive=True, location="riverbank"),
                "F2": SimpleNamespace(alive=True, location="house"),
                "F3": SimpleNamespace(alive=True, location="riverbank"),
            }),
            seeds=SimpleNamespace(
                plants={
                    "R1": {"id": "R1", "kind": "realm", "owner": "F2",
                           "status": "stable", "upkeep": 0.15},
                    "W1": {"id": "W1", "kind": "world", "owner": "F1",
                           "status": "stable", "parent": "R1", "upkeep": 0.11},
                },
                owner_reserve_knowledge={
                    "R1": {"F1": {"tick": 3, "reserve": 0.05}}
                },
                constructs=SimpleNamespace(events=[]),
            ),
            _current_parent="G2:TEST",
        )
        self.sim.log = lambda *args, **kwargs: self.logs.append((args, kwargs))

    def test_voluntary_proposal_does_not_transfer_resources(self):
        before = (dict(self.sim.book.energy), self.sim.book.seq)
        choices = propose_parent_stewardship(self.sim, "F1")
        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0][1], "parent_steward")
        self.assertEqual(choices[0][3], ("R1", 0.6))
        self.assertEqual(before, (dict(self.sim.book.energy), self.sim.book.seq))
        self.sim.book.audit()

    def test_near_target_reserve_preserves_founder_fuel(self):
        # A nearly funded Realm needs a small contribution, not the maximum
        # 0.60 chemical-fuel transfer. This is a voluntary proposal only.
        self.sim.seeds.owner_reserve_knowledge["R1"]["F1"]["reserve"] = 0.68
        self.sim.book.move(energy=[("founder:F1", "reserve:R1", 0.63)],
                           operation_id="setup-near-target")
        before = (dict(self.sim.book.energy), self.sim.book.seq)
        choices = propose_parent_stewardship(self.sim, "F1")
        self.assertEqual(choices[0][3], ("R1", 0.15))
        self.assertEqual(before, (dict(self.sim.book.energy), self.sim.book.seq))
        tend_parent(self.sim, "F1", choices[0][3], "small-shortfall")
        self.assertAlmostEqual(self.sim.book.energy["founder:F1"], 1.22)
        self.sim.book.audit()

    def test_exact_retry_does_not_double_spend_or_duplicate_effects(self):
        first = tend_parent(self.sim, "F1", ("R1", 0.30), "decision-1")
        second = tend_parent(self.sim, "F1", ("R1", 0.30), "decision-1")
        self.assertIs(first, second)
        self.assertEqual(self.sim.book.seq, 1)
        self.assertAlmostEqual(self.sim.book.energy["founder:F1"], 1.70)
        self.assertAlmostEqual(self.sim.book.energy["reserve:R1"], 0.35)
        self.assertEqual(len(self.sim.seeds.constructs.events), 1)
        self.assertEqual(len(self.logs), 1)
        self.assertEqual(self.sim.book.energy["ce:river"], 1.0)
        self.sim.book.audit()

    def test_conflicting_retry_rejected_without_any_side_effect(self):
        tend_parent(self.sim, "F1", ("R1", 0.30), "decision-1")
        before = (dict(self.sim.book.energy), self.sim.book.seq,
                  len(self.sim.seeds.constructs.events), len(self.logs))
        with self.assertRaisesRegex(ValueError, "conflicting operation ID replay"):
            tend_parent(self.sim, "F1", ("R1", 0.40), "decision-1")
        self.assertEqual(before, (dict(self.sim.book.energy), self.sim.book.seq,
                                  len(self.sim.seeds.constructs.events), len(self.logs)))
        self.sim.book.audit()

    def test_subpicounit_conflicting_retry_rejected(self):
        tend_parent(self.sim, "F1", ("R1", 0.30), "decision-1")
        with self.assertRaisesRegex(ValueError, "conflicting operation ID replay"):
            tend_parent(self.sim, "F1", ("R1", 0.3000000000001), "decision-1")
        self.assertEqual(self.sim.book.seq, 1)
        self.sim.book.audit()

    def test_repeat_ack_can_be_returned_after_observation_expires(self):
        first = tend_parent(self.sim, "F1", ("R1", 0.30), "decision-1")
        self.sim.tick += 20
        self.assertIs(tend_parent(self.sim, "F1", ("R1", 0.30), "decision-1"), first)
        self.assertEqual(self.sim.book.seq, 1)
        self.sim.book.audit()

    def test_remote_new_stewardship_rejected_but_prior_receipt_replays(self):
        first = tend_parent(self.sim, "F1", ("R1", 0.30), "local-decision")
        self.sim.founders.people["F1"].location = "ridge"
        before = (dict(self.sim.book.energy), self.sim.book.seq,
                  len(self.sim.seeds.constructs.events), len(self.logs))
        with self.assertRaisesRegex(ValueError, "local physical access"):
            tend_parent(self.sim, "F1", ("R1", 0.20), "remote-decision")
        self.assertEqual(before, (dict(self.sim.book.energy), self.sim.book.seq,
                                  len(self.sim.seeds.constructs.events), len(self.logs)))
        self.assertIs(tend_parent(self.sim, "F1", ("R1", 0.30), "local-decision"), first)
        self.sim.book.audit()

    def test_remote_founder_is_not_offered_impossible_stewardship(self):
        # Existing knowledge can remain fresh after travel, but no physical
        # contribution should be proposed until the Founder returns.
        self.assertTrue(any(p[1] == "parent_steward"
                            for p in propose_parent_stewardship(self.sim, "F1")))
        before = (dict(self.sim.book.energy), self.sim.book.seq,
                  len(self.sim.seeds.constructs.events), len(self.logs))
        self.sim.founders.people["F1"].location = "ridge"
        remote = propose_parent_stewardship(self.sim, "F1")
        # C049 allows a voluntary, Book-funded physical return to observe;
        # still forbid an impossible offsite stewardship transfer.
        self.assertFalse(any(p[1] == "parent_steward" for p in remote))
        self.assertTrue(any(p[1] == "move" and p[3] == "riverbank"
                            for p in remote))
        self.assertEqual(before, (dict(self.sim.book.energy), self.sim.book.seq,
                                  len(self.sim.seeds.constructs.events), len(self.logs)))
        self.sim.founders.people["F1"].location = "riverbank"
        self.assertTrue(any(p[1] == "parent_steward"
                            for p in propose_parent_stewardship(self.sim, "F1")))
        self.sim.book.audit()

    def test_stale_knowledge_rejects_new_contribution(self):
        self.sim.tick += 5
        before = (dict(self.sim.book.energy), self.sim.book.seq)
        with self.assertRaisesRegex(ValueError, "fresh parent reserve observation required"):
            tend_parent(self.sim, "F1", ("R1", 0.30), "new-decision")
        self.assertEqual(before, (dict(self.sim.book.energy), self.sim.book.seq))
        self.assertNotIn("parent:steward:R1:F1:new-decision", self.sim.book.operations)
        self.sim.book.audit()

    def test_founder_retains_minimum_chemical_reserve(self):
        self.sim.book.move(energy=[("founder:F1", "environment:heat", 1.60)])
        before = (dict(self.sim.book.energy), self.sim.book.seq)
        with self.assertRaisesRegex(ValueError, "insufficient existing Founder chemical"):
            tend_parent(self.sim, "F1", ("R1", 0.30), "low-reserve")
        self.assertEqual(before, (dict(self.sim.book.energy), self.sim.book.seq))
        self.sim.book.audit()

    def test_inspection_is_local_and_does_not_mint_energy(self):
        self.sim.seeds.owner_reserve_knowledge["R1"].pop("F1")
        self.sim.founders.people["F1"].location = "ridge"
        with self.assertRaisesRegex(ValueError, "Realm inspection requires"):
            inspect_parent(self.sim, "F1", "R1")
        self.sim.founders.people["F1"].location = "riverbank"
        before = (dict(self.sim.book.energy), self.sim.book.seq)
        inspect_parent(self.sim, "F1", "R1")
        self.assertEqual(self.sim.seeds.owner_reserve_knowledge["R1"]["F1"]["reserve"], 0.05)
        self.assertEqual(before, (dict(self.sim.book.energy), self.sim.book.seq))
        self.sim.book.audit()

    def test_no_dependency_no_stewardship_and_disabled_policy(self):
        self.assertEqual(dependent_parent_ids(self.sim, "F3"), ())
        self.assertEqual(propose_parent_stewardship(self.sim, "F3"), [])
        with self.assertRaisesRegex(ValueError, "not a dependent active parent Realm"):
            tend_parent(self.sim, "F3", ("R1", 0.30), "foreign")
        self.sim.founder_parent_stewardship_enabled = False
        self.assertEqual(propose_parent_stewardship(self.sim, "F1"), [])
        with self.assertRaisesRegex(ValueError, "parent stewardship disabled"):
            tend_parent(self.sim, "F1", ("R1", 0.30), "off")
        self.sim.book.audit()

    def test_collapsed_dependency_no_longer_produces_parent_stewardship(self):
        self.sim.seeds.plants["W1"]["status"] = "collapsed"
        self.assertEqual(dependent_parent_ids(self.sim, "F1"), ())
        self.assertEqual(propose_parent_stewardship(self.sim, "F1"), [])
        self.sim.book.audit()


if __name__ == "__main__":
    unittest.main()
