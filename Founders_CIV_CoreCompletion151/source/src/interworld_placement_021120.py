"""Cycle120: opt-in finite interworld placement comparison; no resource minting."""
import math

def fund_interworld_placement(tree, habitat='floodplain', biomass=2.0, chemical=1.0, transport=0.1):
    if tree.state != 'active' or habitat not in ('floodplain','grassland') or habitat not in tree.habitats:
        raise ValueError('invalid active receiving habitat')
    if getattr(tree,'_interworld_placement_021120',False) or getattr(tree,'_interworld_capacity_021119',False):
        raise ValueError('interworld shipment already funded')
    if any(not math.isfinite(v) or v<=0 or v>10 for v in (biomass,chemical,transport)):
        raise ValueError('invalid bounded shipment')
    book=tree.book; donor='plant:Vespara:forest'; recipient=tree.acct('plant',habitat)
    if donor==recipient or book.mass[donor]<biomass or book.energy['river_pool']<chemical or book.energy['house']<transport:
        raise ValueError('insufficient donor stock')
    before=book.audit()
    book.move(material=[(donor,recipient,biomass)],energy=[('river_pool',tree.acct('chem',habitat),chemical),('house','environment:heat',transport)])
    after=book.audit()
    if after['rejections']!=before['rejections'] or abs(after['mass_error'])>1e-6 or abs(after['energy_error'])>1e-6:
        raise AssertionError('Book conservation failure')
    tree._interworld_placement_021120=habitat
    return {'donor':donor,'recipient':recipient,'biomass':biomass,'chemical':chemical,'transport':transport,'created_mass':0,'created_energy':0}
