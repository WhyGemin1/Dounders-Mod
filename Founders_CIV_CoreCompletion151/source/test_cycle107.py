import pytest
from run_cycle107 import snapshot
class Obj: pass
class Book:
 def audit(self):return {'mass_error':0.,'energy_error':0.,'rejections':0}
def make(tick):
 s=Obj();s.host=Obj();s.host.book=Book();s.host.sim=Obj();s.host.sim.tick=tick;s.bridge=Obj();s.bridge.actors={};s.bridge.tree=Obj();s.bridge.tree.state='active';return s
def test_engine_offset_recorded():
 x=snapshot(make(33),3,30);assert x['engine_day']==33 and x['elapsed_engine_days']==30
def test_clock_drift_rejected():
 with pytest.raises(AssertionError):snapshot(make(34),3,30)
