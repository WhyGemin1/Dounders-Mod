"""Real Core151 headless gateway tests, seed 400. No WorldBox gameplay."""
import unittest
from run_world_tree_pilot import bootstrap
from founders_civ.experimental.worldbox_gateway_m01 import WorldBoxGatewayM01

class M01GatewayTests(unittest.TestCase):
    def setUp(self):
        self.world, _, self.tree_id = bootstrap(400)
        self.tree = self.world.world_trees.worlds[self.tree_id]
        self.gateway = WorldBoxGatewayM01(self.tree)

    def test_one_book_and_clock(self):
        self.assertIs(self.gateway.book, self.world.book)
        self.assertEqual(len(self.world.founders.people), 100)
        before = self.world.tick
        self.world.step()
        self.assertEqual(self.world.tick, before + 1)
        self.world.book.audit()

    def test_harvest_conserves_both_stocks(self):
        h = 'forest'
        m, e = self.tree.acct('plant', h), self.tree.acct('chem', h)
        a, b = self.world.book.mass[m], self.world.book.energy[e]
        self.assertGreater(a, 0.01)
        self.assertGreater(b, 0.001)
        receipt = self.gateway.founder_harvest(
            'F001', 'synthetic-request', '1', h, 'plant', 0.01, 0.001)
        self.assertEqual(receipt.tree_id, self.tree_id)
        self.assertAlmostEqual(self.world.book.mass[m], a - 0.01)
        self.assertAlmostEqual(self.world.book.energy[e], b - 0.001)
        self.assertAlmostEqual(self.world.book.mass['plant:founder:F001'], 0.01)
        self.assertAlmostEqual(self.world.book.energy['chem:founder:F001'], 0.001)
        self.world.book.audit()

    def test_duplicate_rejected_without_transaction(self):
        self.gateway.founder_harvest(
            'F001', 'synthetic-request', '1', 'forest', 'plant', 0.01, 0.001)
        seq = self.world.book.seq
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.gateway.founder_harvest(
                'F001', 'synthetic-request', '1', 'forest', 'plant', 0.01, 0.001)
        self.assertEqual(seq, self.world.book.seq)

    def test_overdraw_atomic(self):
        seq = self.world.book.seq
        with self.assertRaises(ValueError):
            self.gateway.founder_harvest(
                'F001', 'too-large', '1', 'forest', 'plant', 1e9, 0.0)
        self.assertEqual(seq, self.world.book.seq)
        self.world.book.audit()

    def test_invalid_founder_rejected(self):
        seq = self.world.book.seq
        with self.assertRaises(ValueError):
            self.gateway.founder_harvest(
                'FAKE', 'invalid', '1', 'forest', 'plant', 0.01)
        self.assertEqual(seq, self.world.book.seq)

    def test_collapsed_tree_rejected(self):
        self.tree.state = 'archived'
        seq = self.world.book.seq
        with self.assertRaisesRegex(ValueError, 'collapsed'):
            self.gateway.founder_harvest(
                'F001', 'collapsed', '1', 'forest', 'plant', 0.01)
        self.assertEqual(seq, self.world.book.seq)

if __name__ == '__main__':
    unittest.main()
