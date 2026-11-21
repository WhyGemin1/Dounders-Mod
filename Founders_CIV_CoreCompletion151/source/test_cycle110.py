from habitat_bridge import HabitatBridge
from pathlib import Path

def test_opt_in_default():
 assert 'juvenile_energy_conservation=False' in Path(__file__).with_name('src').joinpath('habitat_bridge.py').read_text()

def test_reduced_burn_only_for_offspring():
 source=Path(__file__).with_name('src').joinpath('habitat_bridge.py').read_text()
 assert 'a.parent is not None and a.age<=80' in source
 assert '.00065 if self.juvenile_energy_conservation' in source
