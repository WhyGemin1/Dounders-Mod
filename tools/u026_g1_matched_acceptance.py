"""Executable G1 one-Book matched-seed conservation acceptance.

Runs control and opt-in Tree-food/Founder-harvest/nutrition arms on the actual
Core151 IntegratedWorld. Does not claim ecological stability or live WorldBox.
Fails closed on exceptions, duplicated Book identity, clock drift, or audit.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "Founders_CIV_CoreCompletion151/source/world023024"
sys.path.insert(0, str(ENGINE))
from run_world_tree_pilot import bootstrap  # noqa: E402

SEEDS = (42, 400, 821, 9711, 73, 117, 260, 511, 808, 1009)


def run(seed: int, enabled: bool, days: int) -> dict:
    sim, realm_id, tree_id = bootstrap(seed=seed)
    tree = sim.world_trees.worlds[tree_id]
    if enabled:
        tree.enable_provisioning()
        sim.founder_harvest_enabled = True
        sim.founder_nutrition_enabled = True
    if not (sim.ecology.book is sim.book
            and sim.seeds.constructs.book is sim.book
            and tree.book is sim.book):
        raise AssertionError("G1-A01: more than one authoritative Book")
    snapshots = []
    for day in range(1, days + 1):
        sim.step()
        if sim.tick != sim.ecology.day:
            raise AssertionError("G1-A07: world clocks diverged")
        if day in (30, days):
            audit = sim.book.audit()
            if abs(audit["mass_error"]) > 1e-5 or abs(audit["energy_error"]) > 1e-5:
                raise AssertionError("G1-A03: Book conservation outside tolerance")
            if len(sim.book.asset_ids) > sim.book.transactions:
                raise AssertionError("G1-A04: asset identity count exceeds transactions")
            snapshots.append({
                "day": day, "transactions": sim.book.transactions,
                "operations": len(sim.book.operations),
                "unique_assets": len(sim.book.asset_ids),
                "mass_error": audit["mass_error"],
                "energy_error": audit["energy_error"],
                "tree_status": tree.state,
                "living_tree_population": tree.population,
                "lots": len(tree.provisioning.lots) if tree.provisioning else 0,
            })
    return {"seed": seed, "arm": "g1-enabled" if enabled else "control",
            "days": days, "realm_id": realm_id, "tree_id": tree_id,
            "snapshots": snapshots}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--days", type=int, default=180)
    args = parser.parse_args()
    if not 1 <= args.seeds <= len(SEEDS) or args.days < 30:
        parser.error("seeds must be 1..10 and days >= 30")
    results = []
    for seed in SEEDS[:args.seeds]:
        for enabled in (False, True):
            try:
                row = run(seed, enabled, args.days)
            except Exception as exc:
                print(json.dumps({"gate": "G1", "decision": "FAIL",
                                  "seed": seed, "arm": "g1-enabled" if enabled else "control",
                                  "day_limit": args.days, "error": repr(exc)}), flush=True)
                raise
            results.append(row)
            print(json.dumps({"gate": "G1", "decision": "PASS", **row}), flush=True)
    print(json.dumps({"gate": "G1", "decision": "PASS",
                      "matched_seeds": args.seeds, "arms": 2,
                      "runs": len(results), "horizons": [30, args.days]}), flush=True)


if __name__ == "__main__":
    main()
