"""Opt-in finite interworld plant shipment from existing Vespara forest to Solara floodplain.
This is a relocation of biomass, not creation of global carrying capacity. The source
world loses exactly the biomass delivered. House pays shipping energy and river
funds chemical energy. The two demographic schedulers remain independent.
"""
import math

def fund_interworld_floodplain(tree, biomass=2.0, chemical=1.0, transport=0.1):
    if tree.state != 'active' or 'floodplain' not in tree.habitats:
        raise ValueError('active floodplain required')
    if getattr(tree, '_interworld_capacity_021119', False):
        raise ValueError('already funded')
    if any(not math.isfinite(v) or v <= 0 or v > 10 for v in (biomass,chemical,transport)):
        raise ValueError('finite bounded funding required')
    book=tree.book
    donor='plant:Vespara:forest'
    destination=tree.acct('plant','floodplain')
    chemical_destination=tree.acct('chem','floodplain')
    if donor==destination or book.mass[donor]<biomass or book.energy['river_pool']<chemical or book.energy['house']<transport:
        raise ValueError('insufficient authoritative donor balances')
    before=book.audit()
    book.move(material=[(donor,destination,biomass)],energy=[('river_pool',chemical_destination,chemical),('house','environment:heat',transport)])
    after=book.audit()
    if after['rejections']!=before['rejections'] or abs(after['mass_error'])>1e-6 or abs(after['energy_error'])>1e-6:
        raise AssertionError('Book conservation failure')
    tree._interworld_capacity_021119=True
    return {'biomass_donor':donor,'biomass_recipient':destination,'biomass':biomass,'chemical_donor':'river_pool','chemical':chemical,'transport_donor':'house','transport':transport,'global_biomass_created':0,'transactions':after['transactions']-before['transactions']}
