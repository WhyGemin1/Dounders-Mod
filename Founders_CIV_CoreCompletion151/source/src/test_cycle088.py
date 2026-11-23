from integrated_02188 import Unified288

def test_opt_in_and_control():
    for flag in (False,True):
        s=Unified288(seed=9711,dependent_nutrition=flag)
        assert s.bridge.dependent_nutrition is flag

def test_no_free_nutrition_and_book_audit():
    s=Unified288(seed=9711,dependent_nutrition=True)
    parent=next(a for a in s.bridge.actors.values() if a.sex=='F' and a.stage=='adult')
    # No child: no transfer. Accounting must remain exact.
    before=s.host.book.audit()
    s.bridge._care(parent)
    after=s.host.book.audit()
    assert abs(after['mass_error'])<1e-6
    assert abs(after['energy_error'])<1e-6
    assert after['transactions']>=before['transactions']
