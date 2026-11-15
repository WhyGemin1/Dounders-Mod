import pytest
from integrated_02191 import Unified291
from forage_funding_02191 import ForageFunding

def test_finite_transfer_and_exhaustion():
 s=Unified291(seed=9711,capacity_scale=.5)
 b=s.host.book;p=ForageFunding(budget=1);p.reference=b.mass[s.bridge.tree.acct('plant','floodplain')]*2
 before=b.audit();d=b.mass['plant:Solara:grassland'];out=p.act(s.bridge.tree)
 assert out['funded'] and p.remaining==0
 assert b.mass['plant:Solara:grassland']==pytest.approx(d-.25)
 assert b.audit()['mass_error']==pytest.approx(before['mass_error'],abs=1e-6)
 assert b.audit()['energy_error']==pytest.approx(before['energy_error'],abs=1e-6)
 assert p.act(s.bridge.tree)['reason']=='budget_exhausted'

def test_no_action_without_need():
 s=Unified291(seed=9711,capacity_scale=.5);p=ForageFunding()
 b=s.host.book;before=(dict(b.mass),dict(b.energy))
 assert p.act(s.bridge.tree)['reason']=='forage_sufficient'
 assert before==(dict(b.mass),dict(b.energy))

def test_insufficient_donor_is_atomic():
 s=Unified291(seed=9711,capacity_scale=.5);p=ForageFunding(budget=1,plant_per_action=1e9)
 p.reference=1e10;b=s.host.book;before=(dict(b.mass),dict(b.energy))
 assert not p.act(s.bridge.tree)['funded']
 assert before==(dict(b.mass),dict(b.energy))
