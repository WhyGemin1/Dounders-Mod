"""Read-only U026 C051 phase-1 branch and source ancestry audit.

Requires a clone with fetched origin remote-tracking refs, e.g. GitHub Actions
checkout with fetch-depth: 0. Never infers promotion from branch names or
local branches and never fetches, checks out, merges, pushes or edits Git state.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

BRANCHES = ("Development", "Core", "Integration", "Outer", "main")
SOURCE_PATHS = (
    "Founders_CIV_CoreCompletion151/source/world023024/",
    "Founders_CIV_CoreCompletion151/source/src/core_physiology_v2.py",
    "tools/u026_g2_matched_acceptance.py",
    "docs/U026_G2_CANDIDATE_SOURCE_FINGERPRINT.json",
)


class AuditError(RuntimeError):
    """Incomplete evidence must fail closed, not silently use cached refs."""


def git(repo: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True,
        check=False,
    )
    if process.returncode:
        raise AuditError(
            f"git {' '.join(args)} failed ({process.returncode}): "
            f"{process.stderr.strip()}"
        )
    return process.stdout.strip()


def relation(base_only: int, development_only: int) -> str:
    if base_only and development_only:
        return "diverged"
    if base_only:
        return "development_behind"
    if development_only:
        return "development_ahead"
    return "identical"


def audit(repo: Path) -> dict:
    repo = repo.resolve()
    git(repo, "rev-parse", "--show-toplevel")
    checked_out = git(repo, "rev-parse", "HEAD")
    refs = {}
    for branch in BRANCHES:
        ref = f"refs/remotes/origin/{branch}"
        sha = git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")
        if len(sha) != 40:
            raise AuditError(f"unexpected commit identity for {ref}")
        refs[branch] = {"ref": ref, "sha": sha}
    dev_ref = refs["Development"]["ref"]
    comparisons = {}
    for branch in ("Core", "Integration", "Outer", "main"):
        base_ref = refs[branch]["ref"]
        counts = git(repo, "rev-list", "--left-right", "--count",
                     f"{base_ref}...{dev_ref}").split()
        if len(counts) != 2:
            raise AuditError(f"unable to parse ancestry for {branch}")
        base_only, development_only = map(int, counts)
        comparisons[branch] = {
            "base_only_commits": base_only,
            "development_only_commits": development_only,
            "relation": relation(base_only, development_only),
            "merge_base": git(repo, "merge-base", base_ref, dev_ref),
        }
    sources = {}
    for path in SOURCE_PATHS:
        listing = git(repo, "ls-tree", "-r", "--name-only", dev_ref, "--", path)
        sources[path] = {"present_in_development": bool(listing),
                         "tracked_file_count": len(listing.splitlines()) if listing else 0}
    missing_source = [p for p, item in sources.items() if not item["present_in_development"]]
    role_shas = {branch: refs[branch]["sha"] for branch in ("Core", "Integration", "Outer")}
    return {
        "gate": "U026-C051-PHASE-1",
        "audit": "read_only_origin_refs",
        "checked_out_sha": checked_out,
        "development_checkout_matches_origin": checked_out == refs["Development"]["sha"],
        "branches": refs,
        "comparisons_to_development": comparisons,
        "role_branches_share_head": len(set(role_shas.values())) == 1,
        "tracked_source": sources,
        "missing_required_source": missing_source,
        "mechanical_acceptance": "NOT_RUN",
        "ecological_acceptance": "NOT_RUN",
        "promotion": "NOT_ATTESTED",
        "phase_1_pass": not missing_source,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path,
                        help="Write a reproducible JSON record to the local workspace")
    args = parser.parse_args(argv)
    try:
        result = audit(args.repo)
    except AuditError as exc:
        print(json.dumps({"gate": "U026-C051-PHASE-1", "phase_1_pass": False,
                          "error": str(exc)}, sort_keys=True))
        return 2
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(rendered, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    return 0 if result["phase_1_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
