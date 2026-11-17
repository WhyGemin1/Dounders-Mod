"""Read-only provenance evidence; never bless an experimental hash as baseline."""
from pathlib import Path
import hashlib, json, zipfile

def audit(root:Path, baseline:Path, snapshots:list[Path], member:str):
    root=Path(root); baseline=Path(baseline)
    rel=member.removeprefix('source/world023024/')
    expected=json.loads(baseline.read_text())['hashes'][rel]
    current=hashlib.sha256((root/rel).read_bytes()).hexdigest()
    history=[]
    for archive in snapshots:
        with zipfile.ZipFile(archive) as z:
            data=z.read(member)
        history.append({'archive':Path(archive).name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
    return {'baseline_sha256':expected,'current_sha256':current,'historical_snapshots':history,'baseline_match':current==expected,'all_snapshots_match_current':all(x['sha256']==current for x in history),'conclusion':'drift remains unresolved; matching snapshots do not establish baseline equivalence' if current!=expected else 'hash matches; behavioral validation still required'}
