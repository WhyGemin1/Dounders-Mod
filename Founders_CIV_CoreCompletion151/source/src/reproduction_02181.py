"""Cycle081 experimental post-weaning provisioning: finite parental reserve transfer.
Juveniles can forage independently; nearby parents may subsidize their energy
until maturity, at a strictly bounded maintenance cost to the caregiver.
"""
from reproduction_02180 import ReproductiveBridge280, HERB
from species_life_02115 import PROFILES

class ReproductiveBridge281(ReproductiveBridge280):
    def _care(self, a, episode='primary'):
        super()._care(a,episode)
        if not getattr(self,'juvenile_provisioning',False) or a.species not in HERB or a.stage!='adult':
            return
        donor=self.physical.reserve(a)
        p=PROFILES[a.species]
        # Parents must retain enough energy for eight days of baseline metabolism.
        floor=.004+8*.001*(.5+.5*p.metabolism/.1)
        candidates=[c for c in self.actors.values() if c.alive and c.stage=='juvenile'
                    and c.species==a.species and c.habitat==a.habitat
                    and a.id in c.parent_ids]
        for child in candidates:
            available=max(0.,self.book.energy[donor]-floor)
            target=max(0.,.04-self.book.energy[self.physical.reserve(child)])
            gift=min(.0009,available,target)
            if gift>1e-12:
                self.book.move(energy=[(donor,self.physical.reserve(child),gift)])
