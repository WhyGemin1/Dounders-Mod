from integrated_02176 import Unified276

def test_read_only_book_and_clock():
 s=Unified276(seed=9711,energy_path_audit=True)
 assert s.host.book is s.bridge.book
 s.step()
 assert s.host.sim.tick==s.host.sim.ecology.day
 a=s.host.book.audit()
 assert abs(a['mass_error'])<1e-5 and abs(a['energy_error'])<1e-5

def test_opt_out():
 s=Unified276(seed=9711,energy_path_audit=False)
 s.step()
 assert not s.bridge.energy_path_metrics

def test_opt_in_observes_feeding():
 s=Unified276(seed=9711,energy_path_audit=True)
 for _ in range(3):s.step()
 assert s.bridge.energy_path_metrics['feed_attempts']>0
 assert s.bridge.energy_path_metrics['feed_success']>0
