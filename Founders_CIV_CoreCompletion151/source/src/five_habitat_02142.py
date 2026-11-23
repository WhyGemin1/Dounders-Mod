"""Cycle042: fifth active WORLD-023 habitat funded by the existing Book.

Only the opt-in expansion adds floodplain after the original four-habitat
bootstrap. Native animals, bridge animals, plants and decay use the same
WORLD-023 tree ledger and one host clock. No synthetic resource grant.
"""
from living_tree_runner import LivingTreeRunner
from founders_civ.experimental.world_trees import Habitat

FIFTH = "floodplain"
ORIGINAL = frozenset(('forest','grassland','wetland','ridge'))
MASS_TYPES = ('plant','soil','detritus','water')
ENERGY_TYPES = ('sun','chem')


def add_funded_floodplain(tree, fraction=.16):
    if not 0.0 < fraction < .40:
        raise ValueError('fraction must be inside (0,0.4)')
    if set(tree.habitats) != ORIGINAL:
        raise ValueError('expansion requires exactly the four original habitats')
    if tree.state!='active':
        raise ValueError('five-habitat expansion requires an active World Tree')
    book=tree.book
    mass=[];energy=[]
    # Split both existing stocks, not external Solara or House balances.
    for donor in ('grassland','wetland'):
        for kind in MASS_TYPES:
            q=book.mass[tree.acct(kind,donor)]*fraction
            if q>1e-12:mass.append((tree.acct(kind,donor),tree.acct(kind,FIFTH),q))
        for kind in ENERGY_TYPES:
            q=book.energy[tree.acct(kind,donor)]*fraction
            if q>1e-12:energy.append((tree.acct(kind,donor),tree.acct(kind,FIFTH),q))
    book.move(material=mass, energy=energy)
    tree.habitats[FIFTH]=Habitat(FIFTH,('grassland','wetland'))
    for donor in ('grassland','wetland'):
        old=tree.habitats[donor]
        old.neighbors=(*old.neighbors,FIFTH)
    tree._event('tree_habitat_partition',habitat=FIFTH,
                sources=['grassland','wetland'],fraction=fraction,
                accounts=len(mass)+len(energy))
    tree._snapshot()
    return FIFTH


class FiveHabitatRunner(LivingTreeRunner):
    """Retains original runner's clock/Book auditing, validates 5 habitats."""
    def _validate(self):
        assert self.book is self.sim.ecology.book
        assert self.book is self.sim.world_trees.worlds[self.tree_id].book
        assert len(self.sim.founders.people)==100
        habitats=set(self.sim.world_trees.worlds[self.tree_id].habitats)
        assert habitats in (ORIGINAL, ORIGINAL | {FIFTH})
        assert self.sim.tick==self.sim.ecology.day
        audit=self.book.audit()
        # Book.audit already enforces transaction conservation.  The old
        # hardcoded absolute 1e-6 energy check can fail from accumulated
        # floating-point summation after hundreds of thousands of otherwise
        # balanced transactions over a ~3.2e5-energy ledger.  Retain an
        # *additional* tighter-than-Book scale-aware host guard; never silently
        # overwrite energy accounts or bypass Book.audit.
        assert abs(audit['mass_error'])<1e-6
        assert abs(audit['energy_error'])<max(1e-6,2e-11*audit['energy_total'])
