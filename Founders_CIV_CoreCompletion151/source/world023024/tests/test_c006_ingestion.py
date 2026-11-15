"""C006 historical ingestion contract migrated to C015 per-lot nutrition API.

Tests ownership, opt-in policy, paired Book stocks, no instant Founder
recharge, true-low-fuel ingestion and deterministic checkpoint replay.
"""
import unittest, pickle
from run_world_tree_pilot import bootstrap
from founders_civ.core.founder_harvesting import observed_lots, perform_harvest
from founders_civ.core.founder_nutrition import propose_nutrition, perform_nutrition


class IngestionTests(unittest.TestCase):
    def setUp(self):
        self.sim, _, self.tid = bootstrap(seed=821)
        self.tree = self.sim.world_trees.worlds[self.tid]
        self.tree.enable_provisioning()
        for _ in range(17):
            self.sim.step()
        self.sim.founder_harvest_enabled = True
        self.sim.founder_nutrition_enabled = True
        self.f = 'F001'
        self.sim.founders.people[self.f].location = 'riverbank'
        self.tree.observe(self.f)
        self.tree.observations[self.f]['known_lots'] = observed_lots(self.tree)
        self.lot = next(x['lot'] for x in self.tree.observations[self.f]['known_lots'] if x['kind'] == 'food')

    def harvest(self):
        perform_harvest(self.sim, self.f, (self.tid, self.lot, 'food'))

    def ingest(self, sim=None):
        sim = sim or self.sim
        return perform_nutrition(sim, self.f, 'food_ingest', (self.tid, self.lot))

    def test_cannot_ingest_unowned_food(self):
        self.assertEqual(propose_nutrition(self.sim, self.f), [])
        seq = self.sim.book.seq
        with self.assertRaises(ValueError):
            self.ingest()
        self.assertEqual(self.sim.book.seq, seq)

    def test_ingestion_conserves_and_does_not_recharge(self):
        self.harvest()
        book = self.sim.book
        founder_before = book.energy[f'founder:{self.f}']
        gut = f'gut:founder:{self.f}:lot:{self.lot}'
        gut_energy = f'gut_energy:founder:{self.f}:lot:{self.lot}'
        initial_mass, initial_energy = book.mass.get(gut, 0), book.energy.get(gut_energy, 0)
        self.assertTrue(any(p[1] == 'food_ingest' for p in propose_nutrition(self.sim, self.f)))
        self.ingest()
        self.assertAlmostEqual(book.mass[gut] - initial_mass, .08)
        self.assertAlmostEqual(book.energy[gut_energy] - initial_energy, .02)
        self.assertEqual(book.energy[f'founder:{self.f}'], founder_before)
        self.assertAlmostEqual(book.audit()['mass_error'], 0, places=5)
        self.assertAlmostEqual(book.audit()['energy_error'], 0, places=4)
        self.assertFalse(any(p[1] == 'food_ingest' for p in propose_nutrition(self.sim, self.f)))
        seq = book.seq
        self.ingest()
        self.assertEqual(book.seq, seq)

    def test_low_energy_does_not_block_ingestion(self):
        self.harvest()
        source = f'founder:{self.f}'
        total = self.sim.book.energy[source]
        if total > .01:
            self.sim.book.move(energy=[(source, 'environment:heat', total - .01)])
        choices = self.sim._proposals(self.f, [])
        self.assertTrue(any(p[1] == 'food_ingest' for p in choices))
        self.sim.book.audit()

    def test_checkpoint_replay(self):
        self.harvest()
        frozen = pickle.loads(pickle.dumps(self.sim))
        self.ingest()
        self.ingest(frozen)
        self.assertEqual(dict(self.sim.book.mass), dict(frozen.book.mass))
        self.assertEqual(dict(self.sim.book.energy), dict(frozen.book.energy))
        self.assertEqual(self.sim.book.seq, frozen.book.seq)

    def test_disabled_policy_rejects_ingestion(self):
        self.harvest()
        self.sim.founder_nutrition_enabled = False
        self.assertEqual(propose_nutrition(self.sim, self.f), [])
        with self.assertRaisesRegex(ValueError, 'disabled'):
            self.ingest()
