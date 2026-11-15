from integrated_02175 import Unified275

def test_single_book_and_clock():
 s=Unified275(seed=9711,energy_guard=True)
 assert s.host.book is s.bridge.book
 assert s.host.sim.tick==s.host.sim.ecology.day

def test_guard_off_no_intervention():
 s=Unified275(seed=9711,energy_guard=False)
 s.step()
 assert s.bridge.energy_guard_metrics=={}

def test_guard_observes_finite_energy():
 s=Unified275(seed=9711,energy_guard=True)
 for _ in range(2):s.step()
 assert s.bridge.energy_guard_metrics['evaluations']>0
 a=s.host.book.audit()
 assert abs(a['mass_error'])<1e-5 and abs(a['energy_error'])<1e-5
