from pathlib import Path
import hashlib,json,zipfile
from founders_civ.integration.drift_provenance_069 import audit

def test_drift_is_not_silently_approved(tmp_path):
    root=tmp_path/'root';p=root/'founders_civ/experimental/world_trees.py';p.parent.mkdir(parents=True);p.write_bytes(b'changed')
    baseline=tmp_path/'baseline.json';baseline.write_text(json.dumps({'hashes':{'founders_civ/experimental/world_trees.py':hashlib.sha256(b'original').hexdigest()}}))
    archive=tmp_path/'old.zip'
    with zipfile.ZipFile(archive,'w') as z:z.writestr('source/world023024/founders_civ/experimental/world_trees.py',b'changed')
    result=audit(root,baseline,[archive],'source/world023024/founders_civ/experimental/world_trees.py')
    assert not result['baseline_match']
    assert result['all_snapshots_match_current']
    assert 'unresolved' in result['conclusion']

def test_missing_snapshot_is_error(tmp_path):
    root=tmp_path/'root';p=root/'founders_civ/experimental/world_trees.py';p.parent.mkdir(parents=True);p.write_bytes(b'a')
    baseline=tmp_path/'baseline.json';baseline.write_text(json.dumps({'hashes':{'founders_civ/experimental/world_trees.py':hashlib.sha256(b'a').hexdigest()}}))
    import pytest
    with pytest.raises(FileNotFoundError):audit(root,baseline,[tmp_path/'missing.zip'],'source/world023024/founders_civ/experimental/world_trees.py')
