"""Finite, opt-in fifth-habitat carrying capacity transfers."""
from five_habitat_02142 import FIFTH

def fund_floodplain_capacity(tree, scale=1.0, profile='standard'):
    if FIFTH not in tree.habitats or tree.state != 'active':
        raise ValueError('active five-habitat tree required')
    if not 0 < scale <= 2.0: raise ValueError('scale must be in (0,2]')
    if profile not in ('standard','forage_priority','browse_heavy'): raise ValueError('unknown funding profile')
    if getattr(tree, '_capacity_funded_02145', False): raise ValueError('capacity already funded')
    book=tree.book
    # Same total mass and energy in either profile; forage priority transfers
    # 4 extra units of plant biomass in place of 4 units of soil.
    requested={'plant':{'standard':5.0,'forage_priority':9.0,'browse_heavy':13.0}[profile]*scale,
               'soil':{'standard':12.0,'forage_priority':8.0,'browse_heavy':4.0}[profile]*scale,
               'detritus':1.0*scale,'water':14.0*scale}
    legs=[]
    for kind,quantity in requested.items():
        for donor in ('grassland','wetland'):
            src=f'{kind}:Solara:{donor}';q=quantity/2
            if book.mass[src]+1e-9<q: raise ValueError(f'insufficient external mass: {src}')
            legs.append((src,tree.acct(kind,FIFTH),q))
    chem=2.0*scale;sun=.5*scale;energy=[]
    for donor in ('grassland','wetland'):
        src=f'chem:Solara:{donor}'
        if book.energy[src]+1e-9<chem/2: raise ValueError(f'insufficient external energy: {src}')
        energy.append((src,tree.acct('chem',FIFTH),chem/2))
    if book.energy['house']+1e-9<sun: raise ValueError('insufficient House energy')
    energy.append(('house',tree.acct('sun',FIFTH),sun))
    before=book.audit();book.move(material=legs,energy=energy)
    tree._capacity_funded_02145=True
    tree._event('funded_floodplain_capacity',habitat=FIFTH,scale=scale,profile=profile,
                material=sum(requested.values()),chemical=chem,sun=sun,
                donors=['Solara:grassland','Solara:wetland','house'])
    after=book.audit()
    assert abs(after['mass_error'])<1e-6 and abs(after['energy_error'])<1e-6
    return {'scale':scale,'profile':profile,'mass':sum(requested.values()),
            'energy':chem+sun,'transactions':after['transactions']-before['transactions'],
            'donors':['Solara:grassland','Solara:wetland','house']}
