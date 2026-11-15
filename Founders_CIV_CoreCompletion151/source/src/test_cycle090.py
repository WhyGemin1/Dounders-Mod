import pytest
from integrated_02190 import Unified290
from capacity_policy_02190 import FiniteFloodplainPolicy

def test_policy_no_mint_and_budget():
    s=Unified290(seed=9711,capacity_scale=.5)
    p=FiniteFloodplainPolicy(budget=1,scale=.5,trigger_fraction=.8)
    book=s.host.book; acct=s.bridge.tree.acct('plant','floodplain')
    p.reference=book.mass[acct]*2
    before=book.audit(); donor=book.mass['plant:Solara:grassland']
    out=p.act(s.bridge.tree)
    assert out['funded'] and p.remaining==0
    assert book.mass['plant:Solara:grassland']==pytest.approx(donor-.125)
    assert book.audit()['mass_error']==pytest.approx(before['mass_error'],abs=1e-6)
    assert book.audit()['energy_error']==pytest.approx(before['energy_error'],abs=1e-6)
    snapshot=(dict(book.mass),dict(book.energy))
    assert p.act(s.bridge.tree)['reason']=='budget_exhausted'
    assert snapshot==(dict(book.mass),dict(book.energy))

def test_policy_no_action_when_sufficient():
    s=Unified290(seed=9711,capacity_scale=.5)
    p=FiniteFloodplainPolicy(budget=2)
    before=(dict(s.host.book.mass),dict(s.host.book.energy))
    assert p.act(s.bridge.tree)['reason']=='capacity_sufficient'
    assert p.remaining==2
    assert before==(dict(s.host.book.mass),dict(s.host.book.energy))

def test_policy_validation():
    for kw in ({'budget':-1},{'scale':2},{'trigger_fraction':0}):
        with pytest.raises(ValueError):FiniteFloodplainPolicy(**kw)
