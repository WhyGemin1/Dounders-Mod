from integrated_02174 import Unified274

def test_book_and_clock_shared():
    s=Unified274(seed=9711,adaptive_feeding=True)
    assert s.host.book is s.bridge.book
    assert s.host.sim.tick==s.host.sim.ecology.day

def test_off_keeps_no_adaptive_metrics():
    s=Unified274(seed=9711,adaptive_feeding=False)
    s.step()
    assert s.bridge.feeding_metrics=={}

def test_on_observes_and_conserves():
    s=Unified274(seed=9711,adaptive_feeding=True)
    for _ in range(3): s.step()
    assert s.bridge.feeding_metrics['assessments']>0
    audit=s.host.book.audit()
    assert abs(audit['mass_error'])<1e-5
    assert abs(audit['energy_error'])<1e-5
