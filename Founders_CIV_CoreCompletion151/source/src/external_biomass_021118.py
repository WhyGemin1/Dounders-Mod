"""Opt-in, fail-closed transfer of PRE-EXISTING external plant biomass and energy.
No external material is seeded by this function. Caller must provision an audited donor
through the authoritative Book before freeze; absent donor is a configuration failure.
"""
import math

def fund_external_floodplain(tree, biomass=2.0, energy=1.0, donor='plant:external:founder_store', energy_donor='river_pool'):
    if tree.state != 'active' or 'floodplain' not in tree.habitats:
        raise ValueError('active floodplain required')
    if getattr(tree,'_external_floodplain_funded_021118',False):
        raise ValueError('already funded')
    if not (math.isfinite(biomass) and 0 < biomass <= 10 and math.isfinite(energy) and 0 < energy <= 10):
        raise ValueError('bounded finite amounts required')
    if not donor.startswith('plant:external:') or energy_donor not in ('river_pool','house'):
        raise ValueError('authoritative external donor required')
    b=tree.book
    if b.mass.get(donor,0) < biomass or b.energy.get(energy_donor,0) < energy:
        raise ValueError('insufficient pre-existing external stock')
    before=b.audit()
    b.move(material=[(donor,tree.acct('plant','floodplain'),biomass)],
           energy=[(energy_donor,tree.acct('chem','floodplain'),energy)])
    after=b.audit()
    assert after['rejections']==before['rejections'] and abs(after['mass_error'])<1e-6 and abs(after['energy_error'])<1e-6
    tree._external_floodplain_funded_021118=True
    return {'material_donor':donor,'energy_donor':energy_donor,'mass_debit':biomass,'energy_debit':energy,'transactions':after['transactions']-before['transactions']}
