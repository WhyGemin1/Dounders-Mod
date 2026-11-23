"""C179: observation timestamp validation must fail closed."""
import unittest
from types import SimpleNamespace
from founders_civ.core.founder_harvesting import _recent_observation, MAX_STALENESS


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


if __name__ == '__main__':
    unittest.main()
