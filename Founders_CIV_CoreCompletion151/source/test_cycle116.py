import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from juvenile_foraging_021114 import enable_juvenile_foraging
from species_life_02115 import PROFILES

def test_all_herbivore_species_eligible():
 s=Unified260(seed=9711,counts={k:8 for k in SPECIES})
 b=s.bridge; enable_juvenile_foraging(b)
 assert {'field_mouse','meadow_grazer','forest_browser'}<=set(SPECIES)
 for species in ('field_mouse','meadow_grazer','forest_browser'):
  a=next(x for x in b.actors.values() if x.species==species)
  a.parent='synthetic';a.age=PROFILES[species].independence
  assert a.stage=='juvenile'
  # Simulate the base decision, but run the real overridden decision method.
  base=type(b).__mro__[3]
  old=base.evaluate_needs
  try:
   base.evaluate_needs=lambda self,x:('rest',.2,False)
   account=b.physical.reserve(a)
   energy=b.book.energy[account]
   if energy>.02:b.book.move(energy=[(account,'environment:heat',energy-.02)])
   assert b.book.mass[b.physical.plant(a)]>.04
   before=b.stats['juvenile_foraging_priority']
   assert b.evaluate_needs(a)[0]=='feed'
   assert b.stats['juvenile_foraging_priority']==before+1
  finally:base.evaluate_needs=old
 assert b.book.audit()['rejections']==0

def test_opt_in_off():
 s=Unified260(seed=9711,counts={k:8 for k in SPECIES})
 assert not getattr(s.bridge,'_juvenile_foraging_priority',False)
