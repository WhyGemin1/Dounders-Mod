from types import SimpleNamespace
import pytest
from reproductive_provenance_02132 import audit_bridge_provenance

def test_live_pregnancy_with_recorded_conception():
    a=SimpleNamespace(id='a',species='ridge_hound',alive=True,sex='F',pregnant_until=53,pregnancy_father='b')
    bridge=SimpleNamespace(day=45,actors={'a':a},events=[{'event_id':'1','day':43,'event':'conception','species':'ridge_hound','mother':'a','due':53}])
    result=audit_bridge_provenance(bridge)
    assert result['provenance']['bridge_conception_events']==1
    assert result['provenance']['pregnant_without_recorded_conception']==[]
    assert result['pregnancies']['counts']=={'pending_or_due_unknown':1}

def test_missing_event_is_reported_not_inferred_as_loss():
    a=SimpleNamespace(id='a',species='ridge_hound',alive=True,sex='F',pregnant_until=53,pregnancy_father='b')
    bridge=SimpleNamespace(day=45,actors={'a':a},events=[])
    result=audit_bridge_provenance(bridge)
    assert result['provenance']['pregnant_without_recorded_conception']==['a']
    assert result['pregnancies']['counts']=={}

def test_duplicate_event_ids_rejected():
    bridge=SimpleNamespace(day=45,actors={},events=[{'event_id':'1'},{'event_id':'1'}])
    with pytest.raises(ValueError,match='duplicate'): audit_bridge_provenance(bridge)
