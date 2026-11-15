import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from juvenile_foraging_021114 import enable_juvenile_foraging

def test_priority_changes_real_decision_and_preserves_book():
 s=Unified260(seed=9711,counts={k:8 for k in SPECIES},family_benefits=True)
 b=s.bridge
 a=next(x for x in b.actors.values() if x.species=='field_mouse')
 a.parent='synthetic'; a.age=20
 # Confirm priority can change a real decision without forcing a feed event.
 enable_juvenile_foraging(b)
 seen=False
 for reserve in (.020,.023,.026):
  account=b.physical.reserve(a)
  current=b.book.energy[account]
  if current>reserve:b.book.move(energy=[(account,'environment:heat',current-reserve)])
  elif current<reserve:b.book.move(energy=[('environment:heat',account,reserve-current)])
  before=b.book.audit();action,_,_=b.evaluate_needs(a)
  assert action in ('feed','flee','hide','search','explore','rest','care','mate')
  after=b.book.audit()
  assert before['rejections']==after['rejections']==0
  assert abs(after['energy_error'])<1e-5
  seen |= action=='feed'
 assert seen

def test_default_off():
 s=Unified260(seed=9711,counts={k:8 for k in SPECIES})
 assert not getattr(s.bridge,'_juvenile_foraging_priority',False)
