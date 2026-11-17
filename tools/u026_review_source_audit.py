"""U026 G0/G1/G2 release-candidate fail-closed exact-source audit.

A CANDIDATE attestation, not a declaration of formal Core promotion.
All Git object IDs below are pinned to the accepted Development snapshot.
"""
from __future__ import annotations
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = "Founders_CIV_CoreCompletion151/source/world023024"
EXPECTED = {
    SOURCE: "c70a65a9fdad10eb96e38c6058e7b023da2849b9",
    "tools/u026_g1_matched_acceptance.py": "e1d6f3dfab525a5feb0c154ad57802ee408be0fd",
    "tools/u026_g2_matched_acceptance.py": "716c367c3e85e0bb05d5fa0fafb3f5dd9b85f74a",
}
FORBIDDEN = {".pyc", ".sqlite", ".db", ".dll", ".exe", ".pdb", ".log"}
FORBIDDEN_DIRS = {"__pycache__", "obj", "bin", ".pytest_cache"}

def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()

def main() -> int:
    problems = []
    for path, sha in EXPECTED.items():
        try:
            actual = git("rev-parse", "HEAD:" + path)
            if actual != sha:
                problems.append(f"git tree/blob drift: {path} {actual} != {sha}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            problems.append(f"missing reviewed source object: {path}")
    tracked = git("ls-files", "--", SOURCE).splitlines()
    if not tracked:
        problems.append("release source tree contains no tracked files")
    for path in tracked:
        item = pathlib.Path(path)
        if item.suffix.lower() in FORBIDDEN or any(p in FORBIDDEN_DIRS for p in item.parts):
            problems.append("forbidden generated artifact: " + path)
        if not (ROOT / item).is_file():
            problems.append("missing checked-out file: " + path)
            continue
        expected = git("rev-parse", "HEAD:" + path)
        actual = git("hash-object", "--", path)
        if actual != expected:
            problems.append("working source modification: " + path)
    for path, sha in EXPECTED.items():
        if path == SOURCE:
            continue
        if not (ROOT / path).is_file() or git("hash-object", "--", path) != sha:
            problems.append("matched acceptance script modified: " + path)
    untracked = git("ls-files", "--others", "--exclude-standard", "--", SOURCE).splitlines()
    if untracked:
        problems.append("untracked source files: " + repr(untracked))
    if problems:
        print("U026 G0/G1/G2 RELEASE SOURCE AUDIT FAILED")
        print("\n".join(problems))
        return 1
    print(f"U026 G0/G1/G2 CANDIDATE EXACT SOURCE PASS: {len(tracked)} files; tree {EXPECTED[SOURCE]}")
    print("REVIEW REQUIRED: passing this audit does not promote G0/G1/G2 into Core.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
