from integrated_02182 import Unified282
from species_life_02115 import PROFILES

def test_opt_in_foraging_decision_and_conservation():
 s=Unified282(seed=9711,reproductive_ecology=True,juvenile_foraging=True)
 b=s.bridge
 a=next(x for x in b.actors.values() if x.species=='field_mouse' and x.alive)
 a.age=PROFILES[a.species].independence
 b.book.move(energy=[(b.physical.reserve(a),'environment:heat',b.book.energy[b.physical.reserve(a)]*.8)])
 before=b.book.audit()
 assert b.evaluate_needs(a)[0]=='feed'
 after=b.book.audit()
 assert before['mass_error']==after['mass_error'] and before['energy_error']==after['energy_error']

def test_opt_out():
 s=Unified282(seed=9711,juvenile_foraging=False)
 assert not s.bridge.juvenile_foraging

def test_juvenile_retention_reduces_real_metabolic_debit():
 import pickle
 s=Unified282(seed=9711,reproductive_ecology=True,juvenile_foraging=True)
 b=s.bridge
 a=next(x for x in b.actors.values() if x.species=='field_mouse' and x.alive)
 a.age=PROFILES[a.species].independence
 b.actors={a.id:a}
 before=b.book.energy[b.physical.reserve(a)]
 b._metabolize(a)
 actual=before-b.book.energy[b.physical.reserve(a)]
 expected=.001*(.5+.5*PROFILES[a.species].metabolism/.1)*.40
 assert abs(actual-expected)<1e-10
 assert b.book.audit()['rejections']==0
