"""Static compatibility fingerprints; report drift before importing future code."""
from __future__ import annotations
from pathlib import Path
import hashlib, json

TRACKED=(
 'founders_civ/core/ledger.py',
 'founders_civ/core/engine.py',
 'founders_civ/experimental/founders.py',
 'founders_civ/experimental/social_agents.py',
 'founders_civ/experimental/world_integration.py',
 'founders_civ/experimental/world_trees.py',
 'founders_civ/experimental/world024.py',
 'knowledge_architecture.py',
 'founder_world.html',
 'launch_world024.py',
)

def fingerprint(root:Path):
    return {p:hashlib.sha256((root/p).read_bytes()).hexdigest()
            if (root/p).is_file() else None for p in TRACKED}

def check(root:Path,manifest:Path):
    known=json.loads(manifest.read_text(encoding='utf8'))
    actual=fingerprint(root)
    modified=[p for p in TRACKED if known.get('hashes',{}).get(p)!=actual[p]]
    return {'status':'compatible_fingerprint' if not modified else 'drift_requires_review',
            'changed_files':modified,'current_hashes':actual,
            'warning':'Matching hashes do not prove behavioral compatibility; run tests.'}


class ReviewedDriftError(ValueError):
    """Raised if a reviewed source-drift declaration is malformed."""


def reviewed_check(root: Path, baseline: Path, approval: Path) -> dict:
    """Accept only explicitly reviewed *exact* source hashes.

    The immutable baseline stays unchanged. A missing file, unapproved change,
    stale reference hash, or invalid approval is never silently accepted.
    """
    root, baseline, approval = map(Path, (root, baseline, approval))
    original = json.loads(baseline.read_text(encoding='utf8'))
    attestation = json.loads(approval.read_text(encoding='utf8'))
    if attestation.get('schema') != 'founders-civ-reviewed-drift-v1':
        raise ReviewedDriftError('unrecognized reviewed drift schema')
    declared = attestation.get('approved_changes')
    if not isinstance(declared, dict) or not declared:
        raise ReviewedDriftError('approved_changes must be a nonempty mapping')
    if set(declared) - set(TRACKED):
        raise ReviewedDriftError('approval references nontracked path')
    for path, decision in declared.items():
        if (not isinstance(decision, dict)
                or decision.get('baseline_sha256') != original.get('hashes', {}).get(path)
                or not isinstance(decision.get('approved_sha256'), str)
                or len(decision['approved_sha256']) != 64
                or not decision.get('rationale')):
            raise ReviewedDriftError('invalid or stale review for '+path)
    raw = check(root, baseline)
    changed = set(raw['changed_files'])
    unapproved = sorted(p for p in changed if
                        p not in declared or
                        raw['current_hashes'][p] is None or
                        declared[p]['approved_sha256'] != raw['current_hashes'][p])
    raw['unapproved_files'] = unapproved
    raw['approved_files'] = sorted(changed - set(unapproved))
    raw['status'] = ('drift_requires_review' if unapproved
                     else 'approved_drift' if changed
                     else 'compatible_fingerprint')
    return raw
