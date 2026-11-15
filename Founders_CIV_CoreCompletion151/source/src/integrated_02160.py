"""Cycle060: one opt-in runtime composing verified five-habitat, RSW-K and finite capacity.

No new Book, clock, animal scheduler or resource production. Cell-local branch excluded.
"""
from unified_02142 import Unified242
from funded_capacity_02145 import fund_floodplain_capacity

class Unified260(Unified242):
    def __init__(self, seed=9711, governance='collective', counts=None, *,
                 five_habitats=True, family_benefits=True,
                 resource_aware_family=True, capacity_scale=0.0,
                 grid_size=8, colonize_floodplain=True, capacity_profile="standard"):
        if capacity_scale and not five_habitats:
            raise ValueError('funded floodplain capacity requires fifth habitat')
        super().__init__(seed=seed, governance=governance, counts=counts,
                         five_habitats=five_habitats, family_benefits=family_benefits,
                         resource_aware_family=resource_aware_family,
                         grid_size=grid_size, colonize_floodplain=colonize_floodplain)
        self.capacity_funding = None
        if capacity_scale:
            self.capacity_funding = fund_floodplain_capacity(self.bridge.tree, scale=capacity_scale, profile=capacity_profile)
        self._check()

    def report(self):
        result=super().report()
        result['capacity_funding']=self.capacity_funding
        result['integration_02160']={'single_book': self.host.book is self.bridge.tree.book,
            'single_clock':self.host.sim.tick==self.host.sim.ecology.day,
            'cell_local_branch_merged':False}
        return result
