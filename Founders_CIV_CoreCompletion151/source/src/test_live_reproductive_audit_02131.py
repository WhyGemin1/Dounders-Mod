from types import SimpleNamespace
from live_reproductive_audit_02131 import live_reproductive_audit

def test_species_and_future_event_isolation():
    events=[{'kind':'conception','species':'ridge_hound','mother':'a','day':42,'due':52},
            {'kind':'birth','species':'field_mouse','mother':'a','day':45},
            {'kind':'birth','species':'ridge_hound','mother':'a','day':55}]
    result=live_reproductive_audit(events, {}, 50)
    assert result['pregnancies']['counts']=={'pending_or_due_unknown':1}


def test_death_and_sex_snapshot():
    events=[{'kind':'death','species':'ridge_hound','day':44,'cause':'starvation'}]
    actors={'a':SimpleNamespace(species='ridge_hound',alive=True,sex='female'),
            'b':SimpleNamespace(species='field_mouse',alive=True,sex='male')}
    r=live_reproductive_audit(events, actors, 45, ledger_rejections=0)
    assert r['living_by_sex']=={'female':1}
    assert r['death_causes']=={'starvation':1}
    assert r['ledger_rejections']==0
