from types import SimpleNamespace as N
from generation_audit_021108 import generation_metrics

def test_lineage_counts_and_maturity():
    actors={
      'a':N(id='a',parent=None,age=110,alive=True),
      'b':N(id='b',parent='a',age=80,alive=True),
      'c':N(id='c',parent='a',age=81,alive=True),
      'd':N(id='d',parent='c',age=0,alive=True)}
    bridge=N(actors=actors,events=[{'event':'introduced','actor':'a'},{'event':'birth','actor':'b'},{'event':'birth','actor':'c'},{'event':'birth','actor':'d'}])
    m=generation_metrics(bridge)
    assert (m['g1_adults'],m['g1_living'],m['g1_births'],m['g2_births'])==(1,2,2,1)

def test_missing_parent_rejected():
    import pytest
    bridge=N(actors={'x':N(id='x',parent='missing',age=0,alive=True)},events=[])
    with pytest.raises(ValueError):generation_metrics(bridge)
