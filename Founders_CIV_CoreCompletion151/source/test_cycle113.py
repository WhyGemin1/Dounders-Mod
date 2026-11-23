import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from juvenile_dispatch_021111 import enable_juvenile_conservation
from species_life_02115 import PROFILES

def test_juvenile_dispatch_uses_species_maturity():
    s=Unified260(seed=9711,counts={k:8 for k in SPECIES},family_benefits=True)
    b=s.bridge
    a=next(a for a in b.actors.values() if PROFILES[a.species].maturity>80)
    a.parent='synthetic';a.age=81
    reserve=b.physical.reserve(a)
    enable_juvenile_conservation(b)
    before=b.book.energy[reserve]
    b._metabolize(a)
    demand=.001*(.5+.5*PROFILES[a.species].metabolism/.1)*.65
    assert abs(before-b.book.energy[reserve]-min(before,demand))<1e-10
    assert b.book.audit()['rejections']==0
