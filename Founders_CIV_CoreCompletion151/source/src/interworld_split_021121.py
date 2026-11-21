"""Cycle121 opt-in split finite interworld shipment across two receiving habitats."""
import math

def fund_split_shipment(tree, floodplain_fraction=0.5, biomass=2.0, chemical=1.0, transport=0.1):
    if tree.state != 'active' or not {'floodplain','grassland'}.issubset(tree.habitats):
        raise ValueError('active paired habitats required')
    if getattr(tree,'_interworld_placement_021120',False) or getattr(tree,'_interworld_capacity_021119',False) or getattr(tree,'_interworld_split_021121',False):
        raise ValueError('shipment already funded')
    if not math.isfinite(floodplain_fraction) or not 0 <= floodplain_fraction <= 1:
        raise ValueError('invalid allocation fraction')
    if any(not math.isfinite(v) or v <= 0 or v > 10 for v in (biomass,chemical,transport)):
        raise ValueError('invalid finite shipment')
    book=tree.book
    donor='plant:Vespara:forest'
    if book.mass[donor]<biomass or book.energy['river_pool']<chemical or book.energy['house']<transport:
        raise ValueError('insufficient donor resources')
    f=floodplain_fraction
    material=[(donor,tree.acct('plant',h),q) for h,q in [('floodplain',biomass*f),('grassland',biomass*(1-f))] if q>0]
    energy=[('river_pool',tree.acct('chem',h),q) for h,q in [('floodplain',chemical*f),('grassland',chemical*(1-f))] if q>0]
    energy.append(('house','environment:heat',transport))
    before=book.audit()
    book.move(material=material,energy=energy)
    after=book.audit()
    if after['rejections']!=before['rejections'] or abs(after['mass_error'])>1e-6 or abs(after['energy_error'])>1e-6:
        raise AssertionError('conservation failed')
    tree._interworld_split_021121=f
    return {'fraction':f,'biomass':biomass,'chemical':chemical,'transport':transport,'mass_created':0,'energy_created':0}
