from integrated_02180 import Unified280
from species_life_02115 import PROFILES

def test_diversified_forage_is_finite():
 s=Unified280(seed=9711,reproductive_ecology=True)
 b=s.bridge;h='grassland';plant=b.tree.acct('plant',h)
 before=sum(b.book.mass.values());old=b.book.mass[plant]
 b._diversify(h)
 assert b.book.mass[plant]<old
 assert b.book.mass[f'forage:browse:{h}']>0
 assert abs(sum(b.book.mass.values())-before)<1e-8

def test_juvenile_retention_reduces_real_burn():
 s=Unified280(seed=9711,reproductive_ecology=True)
 b=s.bridge;a=next(a for a in b.actors.values() if a.alive and a.species=='field_mouse')
 a.age=PROFILES[a.species].independence
 key=b.physical.reserve(a);before=b.book.energy[key]
 b._metabolize(a)
 assert 0<before-b.book.energy[key]<.001*(.5+.5*PROFILES[a.species].metabolism/.1)

def test_opt_out_keeps_old_feed():
 s=Unified280(seed=9711,reproductive_ecology=False)
 assert not s.bridge.reproductive_ecology
