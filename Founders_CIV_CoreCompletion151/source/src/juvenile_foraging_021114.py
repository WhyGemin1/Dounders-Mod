"""Cycle114 opt-in juvenile feeding priority, no independent scheduler."""
def enable_juvenile_foraging(bridge):
    if getattr(bridge, '_juvenile_foraging_priority', False):
        raise RuntimeError('already enabled')
    bridge._juvenile_foraging_priority = True
    return bridge
