"""Opt-in external river energy supplement, without minting biomass or energy."""
def fund_river_floodplain_energy(tree, amount=1.0):
    if 'floodplain' not in tree.habitats or tree.state!='active':
        raise ValueError('active floodplain required')
    if not 0 < amount <= 10:raise ValueError('bounded funding required')
    if getattr(tree,'_river_energy_funded_021117',False):
        raise ValueError('duplicate funding')
    b=tree.book
    if b.energy['river_pool'] < amount:raise ValueError('river depleted')
    before=b.audit()
    b.move(energy=[('river_pool',tree.acct('chem','floodplain'),amount)])
    after=b.audit()
    assert after['rejections']==before['rejections'] and abs(after['energy_error'])<1e-6
    tree._river_energy_funded_021117=True
    return {'donor':'river_pool','recipient':tree.acct('chem','floodplain'), 'energy_debit':amount,'energy_credit':amount,'mass_added':0.0}
