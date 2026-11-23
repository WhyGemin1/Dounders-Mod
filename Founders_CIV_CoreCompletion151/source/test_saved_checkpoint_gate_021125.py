import pickle
from saved_checkpoint_gate_021125 import audit_checkpoint
from diagnose_replay_021124 import build

def test_own_checkpoint_matches(tmp_path):
    s=build()
    for _ in range(30):s.step()
    p=tmp_path/'day30.pkl';p.write_bytes(pickle.dumps(s))
    r=audit_checkpoint(p,advance=1)
    assert r['exact_checkpoint'] and r['exact_replay'],r

def test_wrong_seed_is_rejected(tmp_path):
    s=build(seed=9712)
    for _ in range(30):s.step()
    p=tmp_path/'day30.pkl';p.write_bytes(pickle.dumps(s))
    r=audit_checkpoint(p,seed=9711,advance=0)
    assert not r['exact_checkpoint']
