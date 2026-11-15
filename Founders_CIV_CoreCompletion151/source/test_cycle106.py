from run_cycle106 import snapshot
class Book:
 def audit(self):return dict(mass_error=0,energy_error=0,rejections=0)
class Dummy:pass
def test_snapshot_counts_generations():
 s=Dummy();s.host=Dummy();s.host.book=Book();s.host.sim=Dummy();s.host.sim.tick=30;s.bridge=Dummy();s.bridge.tree=Dummy();s.bridge.tree.state='active'
 a=Dummy();a.alive=True;a.generation=1;a.age=200;a.maturity_age=180
 b=Dummy();b.alive=False;b.generation=2
 s.bridge.actors={1:a,2:b}
 r=snapshot(s);assert r['g1_alive']==1 and r['g1_adults']==1 and r['g2_births']==1
