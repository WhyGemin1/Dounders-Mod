"""Reconstruct C004 from SHA-pinned archive and overlay later Development modules.

Run from a checkout; never writes to Core, Integration, Outer, or main.
This is a staging utility, NOT evidence of completed integration.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil, subprocess, sys, zipfile
from pathlib import Path

C004_SHA = "cb3359fb9570eed1d720f14e61dfdffe7d5ecbb683a93a6191c0809ef54e5c0b"
ROOT = Path("Founders_CIV_CoreCompletion151/source/world023024")
LATER = ("founder_nutrition.py", "founder_recovery.py", "founder_tree_agency.py")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def integrate(archive, checkout, output):
    if sha(archive) != C004_SHA:
        raise ValueError("C004 SHA mismatch")
    if output.exists():
        raise ValueError("output must not exist")
    output.mkdir(parents=True)
    with zipfile.ZipFile(archive) as z:
        for member in z.infolist():
            if not (output / member.filename).resolve().is_relative_to(output.resolve()):
                raise ValueError("unsafe ZIP path")
        z.extractall(output)
    source = output / ROOT
    if not (source / "founders_civ/core/ledger.py").is_file():
        raise ValueError("authoritative Book missing")
    changed = []
    for name in LATER:
        rel = ROOT / "founders_civ/core" / name
        src, dst = checkout / rel, output / rel
        if not src.is_file():
            raise FileNotFoundError(str(rel))
        if dst.is_file() and sha(dst) == sha(src):
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        changed.append({"path": str(rel), "sha256": sha(dst)})
    test = subprocess.run([sys.executable, "-m", "unittest", "discover",
                           "-s", "tests", "-q"], cwd=source,
                          capture_output=True, text=True)
    (output / "TEST_OUTPUT.txt").write_text(test.stdout + test.stderr)
    manifest = {"baseline_sha256": C004_SHA, "overlays": changed,
                "tests": "passed" if test.returncode == 0 else "failed",
                "note": "Passing existing tests does not prove integrated runtime wiring."}
    (output / "INTEGRATION_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    if test.returncode:
        raise RuntimeError("tests failed; inspect TEST_OUTPUT.txt")
    return manifest

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("c004_zip", type=Path)
    p.add_argument("development_checkout", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    print(json.dumps(integrate(a.c004_zip, a.development_checkout, a.output), indent=2))
