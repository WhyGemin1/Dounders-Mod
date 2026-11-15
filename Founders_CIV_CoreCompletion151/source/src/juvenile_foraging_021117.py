"""Opt-in juvenile feeding access: real local food and finite Book transfers only."""
from species_life_02115 import PROFILES

def enable_juvenile_feeding_access(bridge):
    if getattr(bridge,'_juvenile_feeding_access',False):
        raise RuntimeError('already enabled')
    bridge._juvenile_feeding_access=True
    original=bridge._feed_herbivore
    def feed(animal):
        # Preserve the native food transfer and all conservation constraints.
        # Young independent herbivores can retry once if the native attempt
        # fails while both local plant and chemical energy remain available.
        result=original(animal)
        if (not result and animal.alive and animal.parent is not None
            and animal.stage=='juvenile' and animal.age<PROFILES[animal.species].maturity
            and animal.species in ('field_mouse','meadow_grazer','forest_browser')
            and bridge.book.mass[bridge.physical.plant(animal)]>.04
            and bridge.book.energy[bridge.physical.chem(animal)]>.0004):
            return original(animal)
        return result
    bridge._feed_herbivore=feed
    return bridge
