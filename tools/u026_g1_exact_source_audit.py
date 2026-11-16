"""Fail-closed U026 G1 acceptance audit. Never rewrite historical G0 attestations.

The candidate manifest is a snapshot of exact source bytes, not a promotion
decision. Any source edit requires a new reviewed candidate and CI rerun.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(".")
MANIFEST = ROOT / "docs/U026_G1_CANDIDATE_SOURCE_FINGERPRINT.json"
data = json.loads(MANIFEST.read_text(encoding="utf-8"))
expected = data["sha256"]
missing = [path for path in sorted(expected) if not (ROOT / path).is_file()]
changed = [path for path in sorted(expected)
           if (ROOT / path).is_file()
           and hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected[path]]

# Newly introduced executable Python under the authoritative Core151 engine
# must be explicitly included, not silently excluded from the source snapshot.
engine = ROOT / "Founders_CIV_CoreCompletion151/source/world023024"
unlisted_python = sorted(
    str(path) for base in (engine / "founders_civ", engine / "tests")
    for path in base.rglob("*.py") if str(path) not in expected
)
bad_suffixes = {".dll", ".pdb", ".pyc", ".sqlite", ".db", ".exe", ".log"}
bad_parts = {"__pycache__", "obj", "bin", ".pytest_cache"}
forbidden = sorted(str(path) for path in ROOT.rglob("*") if path.is_file()
                   and (path.suffix.lower() in bad_suffixes
                        or any(part in bad_parts for part in path.parts)))
result = {
    "gate": "G1-acceptance",
    "source_commit": data.get("source_commit"),
    "manifest_count_valid": data.get("files") == len(expected),
    "expected": len(expected),
    "missing": missing,
    "changed": changed,
    "unlisted_python": unlisted_python,
    "forbidden": forbidden,
}
print(json.dumps(result, indent=2))
sys.exit(0 if (result["manifest_count_valid"] and not any(
    (missing, changed, unlisted_python, forbidden))) else 1)
