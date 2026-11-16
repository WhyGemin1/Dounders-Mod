#!/usr/bin/env python3
"""M01 read-only live before/after WorldBox identity evidence.

Identities are native ActorData.id. Names, tiles and operator-provided world keys
are not substitutes. Paused full snapshots are necessary but not independent
proof of save-slot identity; this report remains a provisional live trial.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_FIELDS = ("native_actor_id", "asset_id", "generation", "parent_id_1", "parent_id_2")


def load_snapshot(path: Path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if (data.get("paused") is not True
        or data.get("world_loading") is not False
        or data.get("has_more") is not False
        or data.get("offset") != 0
        or data.get("missing_identity_count") != 0
        or data.get("duplicate_identity_count") != 0):
        raise ValueError(f"Unusable M01 paused/complete snapshot: {path}")
    rows = data.get("items")
    if not isinstance(rows, list):
        raise ValueError(f"Missing M01 items array: {path}")
    if data.get("matched") != len(rows) or data.get("returned") != len(rows):
        raise ValueError("Partial/inconsistent M01 response counts")
    if len(rows) > 5000:
        raise ValueError("M01 small-world limit exceeded; never truncate identities")
    indexed = {}
    for r in rows:
        if not isinstance(r, dict) or any(field not in r for field in REQUIRED_FIELDS):
            raise ValueError("M01 identity row missing required identity/lineage fields")
        actor_id = str(r["native_actor_id"]).strip()
        species = str(r["asset_id"]).strip()
        if (not actor_id or actor_id.lower() in ("none", "null")
            or not species or species.lower() in ("none", "null")):
            raise ValueError("Empty native ID or species; no name/position fallback")
        if actor_id in indexed:
            raise ValueError(f"Duplicate M01 native actor ID: {actor_id}")
        indexed[actor_id] = r
    return data, indexed


def compare(before: Path, after: Path, minimum=20):
    earlier, b = load_snapshot(before)
    later, a = load_snapshot(after)
    if earlier.get("world_seed") != later.get("world_seed"):
        raise ValueError("Different WorldBox seeds; cannot compare as one saved world")
    if earlier.get("capture_asset_id") != later.get("capture_asset_id"):
        raise ValueError("Different M01 native species cohort filters; repeat both snapshots with the same -AssetId")
    if len(b) < minimum:
        raise ValueError(f"Only {len(b)} before-actors; minimum is {minimum}")
    mismatches = []
    for actor_id, old in b.items():
        if actor_id not in a:
            mismatches.append({"id": actor_id, "reason": "absent_after_reload"})
            continue
        other = a[actor_id]
        changed = [k for k in ("asset_id", "generation", "parent_id_1", "parent_id_2")
                   if old.get(k) != other.get(k)]
        if changed:
            mismatches.append({"id": actor_id, "reason": "identity_or_lineage_changed",
                               "fields": changed})
    added = sorted(set(a) - set(b))
    return {
        "phase": "M01_live_identity_trial",
        "before": str(before), "after": str(after),
        "world_seed_match": True,
        "native_species_cohort": earlier.get("capture_asset_id"),
        "before_actor_count": len(b), "after_actor_count": len(a),
        "matched_actor_count": len(set(a) & set(b)),
        "missing_or_changed": mismatches,
        "new_actor_ids": added,
        "identity_and_lineage_pass": not mismatches and not added,
        "independent_save_identity_verified": False,
        "observer_only": True,
        "limitations": [
            "A matching WorldBox world_seed does not prove the same saved world",
            "This proves neither parentage nor genuine biological birth from callbacks",
            "Do not merge native state into Core151 Book or promote M01 from one trial",
        ],
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("before", type=Path)
    p.add_argument("after", type=Path)
    p.add_argument("--minimum", type=int, default=20)
    p.add_argument("--output", type=Path)
    args = p.parse_args(argv)
    try:
        result = compare(args.before, args.after, args.minimum)
        serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(serialized, encoding="utf-8")
        print(serialized)
        return 0 if result["identity_and_lineage_pass"] else 2
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"phase":"M01_live_identity_trial","decision":"FAIL_CLOSED",
                          "error":str(exc)},indent=2))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
