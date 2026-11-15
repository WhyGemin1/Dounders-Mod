"""Cycle087 experimental juvenile growth allocation: conserved physical food conversion."""
from reproduction_02186 import ReproductiveBridge286
from species_life_02115 import PROFILES

class ReproductiveBridge287(ReproductiveBridge286):
    def _feed_stock(self,a,source,kind):
        if not getattr(self,'growth_allocation',False) or a.stage not in ('dependent','juvenile'):
            return super()._feed_stock(a,source,kind)
        p=PROFILES[a.species]; b=self.book; ph=self.physical
        q=min(p.intake*.012,b.mass[source],max(0.,b.energy[ph.chem(a)]/.80))
        if q<.0004:return False
        target=p.adult_mass()*(.35+.65*min(1,a.age/p.maturity))
        # Allocate 45% (instead of 17%) of actual consumed biomass to growth.
        # The remainder enters gut and detritus; no new material is minted.
        growth=min(q*.45,max(0.,target-b.mass[ph.live(a)]))
        legs=[]
        if growth>1e-12:legs.append((source,ph.live(a),growth))
        if q-growth>1e-12:legs.append((source,ph.gut(a),q-growth))
        ph.convert(legs)
        en=min(b.energy[ph.chem(a)],q*.80)
        if en>0:b.move(energy=[(ph.chem(a),ph.reserve(a),en)])
        gut=b.mass[ph.gut(a)]
        if gut>1e-12:ph.convert([(ph.gut(a),ph.detritus(a),gut)])
        self._log('feeding',actor=a.id,habitat=a.habitat,food_source=kind,mass=q,maternal_mass=0.,growth=growth)
        return True
