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
