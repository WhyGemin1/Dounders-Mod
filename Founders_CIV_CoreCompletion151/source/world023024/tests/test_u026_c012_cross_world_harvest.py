"""U026-C012: never transfer ambiguous local lot IDs between Worlds."""
import unittest
from collections import defaultdict
from types import SimpleNamespace
from founders_civ.core.founder_harvesting import perform_harvest


class CrossWorldHarvestIdentityTests(unittest.TestCase):
    def make_sim(self, duplicate):
        lot = "LOCAL-7"
        record = lambda: SimpleNamespace(kind="food", state="stored")
        def tree(tid):
            resources = SimpleNamespace(harvest_food=lambda lot, founder: "receipt-1")
            return SimpleNamespace(
                id=tid, provisioning=SimpleNamespace(lots={lot: record()}),
                observations={"F1": {"seen_tick": 4, "known_lots": [
                    {"lot": lot, "kind": "food"}]}},
                resources=resources)
        worlds = {"W1": tree("W1")}
        if duplicate:
            worlds["W2"] = tree("W2")
        book = SimpleNamespace(
            operations={}, mass=defaultdict(float),
            energy=defaultdict(float), seq=0)
        book.mass["portable_food:lot:LOCAL-7:tree:W1"] = .08
        logs = []
        sim = SimpleNamespace(
            founder_harvest_enabled=True, tick=4, book=book,
            founders=SimpleNamespace(people={"F1": SimpleNamespace(
                alive=True, location="riverbank")}),
            world_trees=SimpleNamespace(worlds=worlds),
            log=lambda *a, **k: logs.append((a, k)))
        return sim, logs

    def test_duplicate_local_lot_fails_before_book_transfer(self):
        sim, logs = self.make_sim(True)
        before = (sim.book.seq, dict(sim.book.mass))
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            perform_harvest(sim, "F1", ("W1", "LOCAL-7", "food"))
        self.assertEqual(before, (sim.book.seq, dict(sim.book.mass)))
        self.assertEqual(logs, [])
        self.assertEqual(sim.world_trees.worlds["W1"].provisioning.lots[
            "LOCAL-7"].state, "stored")

    def test_unique_local_lot_remains_harvestable(self):
        sim, logs = self.make_sim(False)
        self.assertEqual(perform_harvest(
            sim, "F1", ("W1", "LOCAL-7", "food")), "receipt-1")
        self.assertEqual(len(logs), 1)
        self.assertEqual(sim.world_trees.worlds["W1"].provisioning.lots[
            "LOCAL-7"].state, "transferred")


if __name__ == "__main__":
    unittest.main()
