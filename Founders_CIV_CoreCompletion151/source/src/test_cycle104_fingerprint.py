from pathlib import Path
import json, hashlib
from founders_civ.integration.compat import check, TRACKED

def test_fingerprint_clean_and_tampered(tmp_path):
    root=tmp_path/'world';root.mkdir()
    hashes={}
    for name in TRACKED:
        f=root/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b'original')
        hashes[name]=hashlib.sha256(b'original').hexdigest()
    manifest=tmp_path/'baseline.json';manifest.write_text(json.dumps({'hashes':hashes}))
    assert check(root,manifest)['status']=='compatible_fingerprint'
    target=root/'founder_world.html';target.write_bytes(b'changed')
    result=check(root,manifest)
    assert result['status']=='drift_requires_review'
    assert result['changed_files']==['founder_world.html']
    assert hashes['founder_world.html']!=result['current_hashes']['founder_world.html']
