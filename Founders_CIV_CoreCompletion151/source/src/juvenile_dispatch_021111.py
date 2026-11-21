"""Cycle112 opt-in juvenile metabolism retaining family-pair support."""
def enable_juvenile_conservation(bridge, multiplier=.65):
    if not (0 < multiplier <= 1):
        raise ValueError('invalid multiplier')
    if getattr(bridge, '_juvenile_dispatch_enabled', False):
        raise RuntimeError('already enabled')
    bridge._juvenile_metabolic_multiplier = multiplier
    bridge._juvenile_dispatch_enabled = True
    return bridge
