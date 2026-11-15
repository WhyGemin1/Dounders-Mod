import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from juvenile_foraging_021114 import enable_juvenile_foraging

def test_opt_in_priority_preserves_book():
 s=Unified260(seed=9711,counts={k:8 for k in SPECIES},family_benefits=True)
 b=s.bridge
 a=next(x for x in b.actors.values() if x.species=='field_mouse')
 a.parent='synthetic'; a.age=100
 b.book.move(energy=[(b.physical.reserve(a),'environment:heat',.018)])
 enable_juvenile_foraging(b)
 before=b.book.audit()
 action,*_=b.evaluate_needs(a)
 assert action in ('feed','flee','hide')
 after=b.book.audit()
 assert after['rejections']==before['rejections']==0
 assert abs(after['mass_error'])<1e-5 and abs(after['energy_error'])<1e-5

def test_default_off():
 s=Unified260(seed=9711,counts={k:8 for k in SPECIES})
 assert not getattr(s.bridge,'_juvenile_foraging_priority',False)
