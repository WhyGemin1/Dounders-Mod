"""C179: observation timestamp validation must fail closed."""
import unittest
from types import SimpleNamespace
from collections import defaultdict
from founders_civ.core.founder_harvesting import _recent_observation, _known_entries, propose_harvest, MAX_STALENESS


class ObservationTimestampTests(unittest.TestCase):
    def test_valid_window_and_bounds(self):
        sim = SimpleNamespace(tick=20)
        for age in (0, 1, MAX_STALENESS):
            self.assertTrue(_recent_observation(sim, {'seen_tick': 20-age}))
        self.assertFalse(_recent_observation(sim, {'seen_tick': 20-MAX_STALENESS-1}))

    def test_corrupt_timestamps_fail_closed(self):
        sim = SimpleNamespace(tick=20)
        for value in (True, False, 20.0, '20', None, -1, 21):
            self.assertFalse(_recent_observation(sim, {'seen_tick': value}))
        self.assertFalse(_recent_observation(sim, None))
        self.assertFalse(_recent_observation(sim, []))
        self.assertFalse(_recent_observation(sim, {}))

    def test_invalid_scheduler_tick_fails_closed(self):
        for tick in (True, 20.0, '20', None):
            self.assertFalse(_recent_observation(SimpleNamespace(tick=tick), {'seen_tick': 20}))


    def test_malformed_lot_collections_fail_closed(self):
        for value in (None, True, 4, 'lot', {'lot': 'x'}, [None, 3, False]):
            with self.subTest(value=repr(value)):
                self.assertEqual(_known_entries({'known_lots': value}), ())
        self.assertEqual(_known_entries({'known_lots': [
            None, 'broken', {'kind': 'food'}, {'lot': 5, 'kind': 'food'},
            {'lot': 'valid', 'kind': 'food'}]}),
            ({'lot': 'valid', 'kind': 'food'},))

    def test_proposals_ignore_malformed_observations(self):
        founder = 'f1'
        tree = SimpleNamespace(observations={founder: {
            'seen_tick': 10, 'known_lots': [None, 3,
            {'lot': 'food-1', 'kind': 'food'}]}})
        sim = SimpleNamespace(founder_harvest_enabled=True, tick=10,
            founders=SimpleNamespace(people={founder: SimpleNamespace(
                alive=True, location='riverbank')}),
            states={founder: SimpleNamespace(main_goal='security')},
            book=SimpleNamespace(energy=defaultdict(float)),
            world_trees=SimpleNamespace(worlds={'tree1': tree}))
        proposals = propose_harvest(sim, founder)
        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0][-1], ('tree1', 'food-1', 'food'))
        tree.observations[founder]['known_lots'] = 'corrupted'
        self.assertEqual(propose_harvest(sim, founder), [])

if __name__ == '__main__':
    unittest.main()
