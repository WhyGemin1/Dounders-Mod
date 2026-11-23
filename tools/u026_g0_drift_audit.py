"""Fail-closed G0 source audit; does not approve changed fingerprints."""
import hashlib, json, pathlib, sys
root = pathlib.Path(".")
manifest = json.loads((root / "docs/U026_C018_SOURCE_FINGERPRINT.json").read_text())
expected = manifest["sha256"]
missing = [p for p in sorted(expected) if not (root / p).is_file()]
changed = [p for p in sorted(expected) if (root / p).is_file() and hashlib.sha256((root / p).read_bytes()).hexdigest() != expected[p]]
bad_suffix = {".dll", ".pdb", ".pyc", ".sqlite", ".db", ".exe", ".log"}
bad_parts = {"__pycache__", "obj", "bin", ".pytest_cache"}
forbidden = sorted(str(p) for p in root.rglob("*") if p.is_file() and (p.suffix.lower() in bad_suffix or any(x in bad_parts for x in p.parts)))
result = {"expected":len(expected),"manifest_count_valid":manifest.get("files")==len(expected),"missing":missing,"changed":changed,"forbidden":forbidden}
print(json.dumps(result,indent=2))
sys.exit(0 if result["manifest_count_valid"] and not (missing or changed or forbidden) else 1)
