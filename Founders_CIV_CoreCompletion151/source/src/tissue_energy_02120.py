"""Opt-in, conservation-first embodied energy pilot; not yet coupled to demographic scheduler.

No energy is minted: plant tissue is funded by a chemical-energy debit; eating
moves energy from tissue to animal reserve and environmental heat. Carrion retains
remaining embodied energy until scavenged or dissipated. A Book is supplied by caller.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class Digestion:
    consumed: float
    assimilated: float
    heat: float

def fund_tissue(book, chem_account, tissue_account, energy):
    if energy < 0: raise ValueError('negative energy')
    if energy: book.move(energy=[(chem_account,tissue_account,energy)])

def digest(book, tissue_account, animal_account, energy, efficiency):
    if energy < 0 or not 0 <= efficiency <= 1: raise ValueError('invalid digestion')
    assimilated=energy*efficiency
    heat=energy-assimilated
    if energy:
        legs=[]
        if assimilated: legs.append((tissue_account,animal_account,assimilated))
        if heat: legs.append((tissue_account,'environment:heat',heat))
        book.move(energy=legs)
    return Digestion(energy,assimilated,heat)

def move_carcass(book, live_tissue, carrion_tissue, energy):
    if energy < 0: raise ValueError('negative energy')
    if energy:book.move(energy=[(live_tissue,carrion_tissue,energy)])

def decay(book, carrion_tissue, energy):
    if energy < 0: raise ValueError('negative energy')
    if energy:book.move(energy=[(carrion_tissue,'environment:heat',energy)])
