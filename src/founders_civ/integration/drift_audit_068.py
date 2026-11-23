"""Read-only compatibility drift attestation; never rewrites historical baseline."""
from __future__ import annotations
import json
from pathlib import Path
from .compat import check


def attest(root: Path, baseline: Path) -> dict:
    root, baseline = Path(root), Path(baseline)
    outcome = check(root, baseline)
    recorded = json.loads(baseline.read_text(encoding='utf8')).get('hashes', {})
    return {
        'status': outcome['status'],
        'changes': [{'path': p, 'baseline_sha256': recorded.get(p),
                     'current_sha256': outcome['current_hashes'].get(p)}
                    for p in outcome['changed_files']],
        'baseline_modified': False,
        'safe_to_promote': outcome['status'] == 'compatible_fingerprint',
    }
