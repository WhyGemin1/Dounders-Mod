from pathlib import Path
import json
from founders_civ.integration.compat import check, fingerprint
from founders_civ.integration.drift_audit_068 import attest


def test_identical_snapshot_is_compatible(tmp_path):
    p=tmp_path/'founders_civ/experimental/world_trees.py'
    p.parent.mkdir(parents=True)
    p.write_text('baseline')
    baseline=tmp_path/'baseline.json'
    baseline.write_text(json.dumps({'hashes':fingerprint(tmp_path)}))
    assert check(tmp_path,baseline)['status']=='compatible_fingerprint'
    p.write_text('experimental modification')
    result=attest(tmp_path,baseline)
    assert result['status']=='drift_requires_review'
    assert result['safe_to_promote'] is False
    assert result['changes'][0]['path']=='founders_civ/experimental/world_trees.py'
