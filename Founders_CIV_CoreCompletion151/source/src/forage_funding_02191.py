"""Cycle091 opt-in forage-directed Founder maintenance, finite Book debits."""
class ForageFunding:
    def __init__(self, budget=3, plant_per_action=.5, energy_per_action=.1, trigger_fraction=.8):
        if not isinstance(budget,int) or budget<0: raise ValueError('budget')
        if min(plant_per_action,energy_per_action,trigger_fraction)<=0 or trigger_fraction>1: raise ValueError('parameters')
        self.remaining=budget; self.plant=plant_per_action; self.energy=energy_per_action
        self.trigger=trigger_fraction; self.reference=None
    def act(self,tree):
        if tree.state!='active' or 'floodplain' not in tree.habitats:return {'funded':False,'reason':'inactive_or_missing'}
        b=tree.book; dest=tree.acct('plant','floodplain'); current=b.mass[dest]
        if self.reference is None:self.reference=current
        if not self.remaining:return {'funded':False,'reason':'budget_exhausted'}
        if current>=self.reference*self.trigger:return {'funded':False,'reason':'forage_sufficient'}
        donors=[f'plant:Solara:{h}' for h in ('grassland','wetland')]
        edonors=[f'chem:Solara:{h}' for h in ('grassland','wetland')]
        q=self.plant/2; e=self.energy/2
        if any(b.mass[d]<q+1e-9 for d in donors):return {'funded':False,'reason':'donor_plant_depleted'}
        if any(b.energy[d]<e+1e-9 for d in edonors):return {'funded':False,'reason':'donor_energy_depleted'}
        before=b.audit()
        b.move(material=[(d,dest,q) for d in donors],energy=[(d,tree.acct('chem','floodplain'),e) for d in edonors])
        after=b.audit()
        assert abs(after['mass_error']-before['mass_error'])<1e-6
        assert abs(after['energy_error']-before['energy_error'])<1e-6
        self.remaining-=1
        return {'funded':True,'mass':self.plant,'energy':self.energy,'remaining':self.remaining}
