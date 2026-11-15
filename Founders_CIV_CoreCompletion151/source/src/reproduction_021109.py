"""Opt-in parental investment: parent pays a finite energy contribution at birth.
No change to existing demographic scheduler or Book ownership.
"""
def birth_with_parental_investment(bridge, parent, *, contribution=0.003):
    if not parent.alive or parent.age <= 80:
        return None
    account=f'animal:{parent.id}'
    if bridge.book.energy[account] < contribution + .0005:
        return None
    offspring=bridge._new(parent.species,parent.habitat,parent=parent.id)
    if offspring is None:
        return None
    bridge.book.move(energy=[(account,f'animal:{offspring.id}',contribution)])
    offspring.energy=bridge.book.energy[f'animal:{offspring.id}']
    return offspring
