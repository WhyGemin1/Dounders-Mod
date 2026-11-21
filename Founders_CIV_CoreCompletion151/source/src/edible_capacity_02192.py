"""Opt-in finite external donor -> immediately edible floodplain forage.

Physical Book transfers, not new primary production.  Founder maintenance is
represented as a bounded authorization; no canonical scheduler is modified.
"""
from forage_funding_02191 import ForageFunding

class EdibleCapacity(ForageFunding):
    def __init__(self,budget=3,plant_per_action=.5,energy_per_action=.1,trigger_fraction=.8):
        super().__init__(budget,plant_per_action,energy_per_action,trigger_fraction)
        self.reference=None

    def act(self,tree):
        if tree.state!='active' or 'floodplain' not in tree.habitats:
            return {'funded':False,'reason':'inactive_or_missing'}
        b=tree.book
        browse='forage:browse:floodplain'; seeds='forage:seeds:floodplain'
        available=b.mass[browse]+b.mass[seeds]
        if self.reference is None:self.reference=max(available,.024)
        if not self.remaining:return {'funded':False,'reason':'budget_exhausted'}
        if available>=self.reference*self.trigger:return {'funded':False,'reason':'forage_sufficient'}
        donors=[f'plant:Solara:{h}' for h in ('grassland','wetland')]
        edonors=[f'chem:Solara:{h}' for h in ('grassland','wetland')]
        q=self.plant/2;e=self.energy/2
        if any(b.mass[d]<q+1e-9 for d in donors):return {'funded':False,'reason':'donor_plant_depleted'}
        if any(b.energy[d]<e+.0001+1e-9 for d in edonors):return {'funded':False,'reason':'donor_energy_depleted'}
        work_source=tree.acct('sun','forest')
        if b.energy[work_source]<.0001:return {'funded':False,'reason':'work_unavailable'}
        before=b.audit()
        b.transform(material=[(donors[0],browse,q),(donors[1],seeds,q)],
                    source=work_source,work=.0001,
                    energy_outputs=[(work_source,'environment:heat',.00009),
                                    (edonors[0],tree.acct('chem','floodplain'),e),
                                    (edonors[1],tree.acct('chem','floodplain'),e)])
        after=b.audit()
        assert abs(after['mass_error']-before['mass_error'])<1e-6
        assert abs(after['energy_error']-before['energy_error'])<1e-6
        self.remaining-=1
        return {'funded':True,'mass':self.plant,'energy':self.energy,
                'remaining':self.remaining,'browse':q,'seeds':q}
