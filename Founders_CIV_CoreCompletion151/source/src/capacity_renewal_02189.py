"""Cycle089: finite, opt-in periodic floodplain maintenance from donor stocks."""

def renew_floodplain(tree, scale=.1):
    if tree.state != 'active' or 'floodplain' not in tree.habitats:
        return {'funded':False,'reason':'inactive_or_missing'}
    if not 0 < scale <= 1: raise ValueError('scale out of range')
    book=tree.book
    mass=[]; energy=[]
    for kind,amount in (('plant',.5),('soil',.8),('water',1.0),('detritus',.1)):
        for donor in ('grassland','wetland'):
            src=f'{kind}:Solara:{donor}'
            q=amount*scale/2
            if book.mass[src] < q+1e-9: return {'funded':False,'reason':'donor_depleted'}
            mass.append((src,tree.acct(kind,'floodplain'),q))
    for donor in ('grassland','wetland'):
        src=f'chem:Solara:{donor}'; q=.2*scale/2
        if book.energy[src]<q+1e-9:return {'funded':False,'reason':'energy_depleted'}
        energy.append((src,tree.acct('chem','floodplain'),q))
    if book.energy['house'] < .05*scale+1e-9:
        return {'funded':False,'reason':'house_depleted'}
    energy.append(('house',tree.acct('sun','floodplain'),.05*scale))
    before=book.audit()
    book.move(material=mass,energy=energy)
    after=book.audit()
    assert abs(after['mass_error']-before['mass_error'])<1e-6
    assert abs(after['energy_error']-before['energy_error'])<1e-6
    return {'funded':True,'mass':2.4*scale,'energy':.25*scale,'transactions':after['transactions']-before['transactions']}
