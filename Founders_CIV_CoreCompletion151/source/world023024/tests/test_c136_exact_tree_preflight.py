"""C136: exact preflight conservation guards for Tree planting and Species admission."""
from collections import defaultdict
from types import SimpleNamespace

import pytest

from founders_civ.experimental.world_trees import (
    WorldTree, START, START_CHEM, START_SUN, BIOMES,
    INITIAL_RESIDENTS_PER_HABITAT,
)


def funded_book():
    mass, energy = defaultdict(float), defaultdict(float)
    for biome in BIOMES:
        for kind, amount in START.items():
            mass[f'{kind}:Solara:{biome}'] = amount
        energy[f'chem:Solara:{biome}'] = START_CHEM
    energy['house'] = len(BIOMES) * START_SUN
    return SimpleNamespace(mass=mass, energy=energy)


@pytest.mark.parametrize('resource', ['soil', 'chem', 'house'])
def test_tree_preflight_rejects_subnanounit_shortfall_without_mutation(resource):
    book = funded_book()
    if resource == 'soil':
        book.mass['soil:Solara:forest'] = START['soil'] - 5e-9
    elif resource == 'chem':
        book.energy['chem:Solara:forest'] = START_CHEM - 5e-9
    else:
        book.energy['house'] = len(BIOMES) * START_SUN - 5e-9
    before_mass, before_energy = dict(book.mass), dict(book.energy)
    with pytest.raises(ValueError, match='unavailable'):
        WorldTree.preflight(book)
    assert dict(book.mass) == before_mass
    assert dict(book.energy) == before_energy


@pytest.mark.parametrize('resource', ['plant', 'sun', 'chem'])
def test_species_preflight_rejects_subnanounit_shortfall(resource):
    tree = WorldTree.__new__(WorldTree)
    tree.id = 'WORLD-TEST'
    tree.state = 'active'
    tree.species_seed_ids = []
    tree.book = SimpleNamespace(mass=defaultdict(float), energy=defaultdict(float))
    count = INITIAL_RESIDENTS_PER_HABITAT
    for biome in BIOMES:
        tree.book.mass[tree.acct('plant', biome)] = count * (.11 + .19)
        tree.book.energy[tree.acct('sun', biome)] = count * .018
        tree.book.energy[tree.acct('chem', biome)] = count * .045
    account = tree.acct(resource, 'forest')
    target = tree.book.mass if resource == 'plant' else tree.book.energy
    target[account] -= 5e-10
    before_mass, before_energy = dict(tree.book.mass), dict(tree.book.energy)
    with pytest.raises(ValueError, match='lacks living habitat resources'):
        tree.preflight_species()
    assert dict(tree.book.mass) == before_mass
    assert dict(tree.book.energy) == before_energy
