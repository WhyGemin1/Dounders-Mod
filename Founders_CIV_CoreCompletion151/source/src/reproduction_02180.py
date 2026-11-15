"""Cycle080: opt-in juvenile retention and diversified, finite plant forage.
Plant forage is split into browse and seed pools by transfers from the single
WORLD-023 plant account. No new primary production or free chemical energy.
"""
from energy_budget_02179 import EnergyBudgetBridge279
from species_life_02115 import PROFILES

HERB=('field_mouse','meadow_grazer','forest_browser')
class ReproductiveBridge280(EnergyBudgetBridge279):
    def _metabolize(self,a):
        if not getattr(self,'reproductive_ecology',False) or a.species not in HERB or a.stage not in ('dependent','juvenile'):
            return super()._metabolize(a)
        # Juvenile torpor: energy conserved, at a cost to condition recovery.
        p=PROFILES[a.species];reserve=self.physical.reserve(a)
        available=self.book.energy[reserve];demand=.001*(.5+.5*p.metabolism/.1)*.55
        burn=min(available,demand)
        if burn:self.book.move(energy=[(reserve,'environment:heat',burn)])
        a.condition=min(1.,a.condition+.002) if burn>=.8*demand else max(0.,a.condition-.035)

    def _diversify(self,habitat):
        plant=self.tree.acct('plant',habitat)
        # Two physically distinct edible stocks, regenerated only by diverting
        # existing plant biomass. Their chemical energy remains in tree chem.
        for kind,share in (('browse',.008),('seeds',.004)):
            acct=f'forage:{kind}:{habitat}'
            q=min(share,max(0.,self.book.mass[plant]-.045))
            if q>0:self.physical.convert([(plant,acct,q)])

    def _feed_herbivore(self,a):
        if not getattr(self,'reproductive_ecology',False) or a.species not in HERB:
            return super()._feed_herbivore(a)
        preferred=('seeds','browse') if a.species=='field_mouse' else ('browse','seeds')
        for kind in preferred:
            acct=f'forage:{kind}:{a.habitat}'
            if self.book.mass[acct]>=.0004 and self._feed_stock(a,acct,kind):return True
        return super()._feed_herbivore(a)

    def step(self,tick):
        if getattr(self,'reproductive_ecology',False) and self.tree.state in ('active','germinating'):
            for habitat in self.tree.habitats:self._diversify(habitat)
        return super().step(tick)
