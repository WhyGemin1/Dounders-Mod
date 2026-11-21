"""Source-adapted Cycle007 field-mouse satiation hysteresis.

This is a small, opt-in *decision gate*, not a second biology engine.
All physical reserves remain owned by WORLD-023 Book.  The two threshold
rules come from the alternative agent's stateful_mouse_needs.py; the
reserve target is taken from the current species NEEDS table.
"""
from species_life_02115 import NEEDS

LOW_FRACTION = 0.82


def mouse_hunger_transition(reserve_energy: float, hungry: bool) -> bool:
    """Return next persistent hunger state, no mutation or energy transfers."""
    if reserve_energy < 0:
        raise ValueError('negative physical reserve')
    target = .035 * NEEDS['field_mouse'][7]
    low = target * LOW_FRACTION
    high = target * max(1.0, NEEDS['field_mouse'][7])
    if reserve_energy <= low:
        return True
    if reserve_energy >= high:
        return False
    return bool(hungry)
