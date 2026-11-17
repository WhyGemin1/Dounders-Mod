import json
from pathlib import Path
from founders_civ.integration.drift_audit_068 import attest


def test_unmodified_tree(tmp_path):
    p = tmp_path / 'founders_civ/experimental/world_trees.py'
    p.parent.mkdir(parents=True)
    p.write_text('original')
    from founders_civ.integration.compat import fingerprint
    baseline = tmp_path / 'baseline.json'
    baseline.write_text(json.dumps({'hashes': fingerprint(tmp_path)}))
    assert attest(tmp_path, baseline)['safe_to_promote']
    p.write_text('changed')
    outcome = attest(tmp_path, baseline)
    assert outcome['status'] == 'drift_requires_review'
    assert not outcome['safe_to_promote']
    assert outcome['changes'][0]['path'] == 'founders_civ/experimental/world_trees.py'
    assert json.loads(baseline.read_text())['hashes']['founders_civ/experimental/world_trees.py'] != outcome['changes'][0]['current_sha256']
