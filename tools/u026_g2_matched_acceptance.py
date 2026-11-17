"""U026 G2 offline matched acceptance on the actual Core151 integrated engine.

G1-funded Tree supply is the control. The G2 arm adds voluntary Founder
Tree agency, local observations, parent stewardship, free decisions and
consensual exchange. Neither arm writes into WorldBox. An ecological failure
is recorded as an outcome, not hidden by forced Founder actions.
"""
from __future__ import annotations
import argparse
import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "Founders_CIV_CoreCompletion151/source/world023024"
sys.path.insert(0, str(ENGINE))
from run_world_tree_pilot import bootstrap  # noqa: E402

SEEDS = (42, 400, 821, 9711, 73, 117, 260, 511, 808, 1009)
EPS = 1e-5


def _audit(sim, founders, tree):
    if not (sim.book is sim.ecology.book
            and sim.book is sim.seeds.constructs.book
            and tree.book is sim.book):
        raise AssertionError("G2 multiple Book authorities")
    if sim.tick != sim.ecology.day:
        raise AssertionError("G2 integrated clocks diverged")
    if set(sim.founders.people) != founders or len(founders) != 100:
        raise AssertionError("G2 Founder identity set drift")
    if len({p.id for p in sim.founders.people.values()}) != 100:
        raise AssertionError("G2 duplicate Founder identity")
    audit = sim.book.audit()
    if abs(audit["mass_error"]) > EPS or abs(audit["energy_error"]) > EPS:
        raise AssertionError("G2 Book conservation tolerance exceeded")
    if sim.book.energy["river_pool"] < -EPS:
        raise AssertionError("G2 finite river Creation Energy overdraft")
    return audit


def _snapshot(sim, tree, day):
    founders = set(sim.founders.people)
    audit = _audit(sim, founders, tree)
    lots = tree.provisioning.lots if tree.provisioning else {}
    states = {}
    for lot in lots.values():
        states[lot.state] = states.get(lot.state, 0) + 1
    return {
        "day": day,
        "book_seq": sim.book.seq,
        "asset_ids": len(sim.book.asset_ids),
        "mass_error": audit["mass_error"],
        "energy_error": audit["energy_error"],
        "river_pool": sim.book.energy["river_pool"],
        "tree_status": tree.state,
        "tree_population": tree.population,
        "births": tree.counters["tree_birth"],
        "deaths": tree.counters["tree_death"],
        "lot_states": states,
        "founders": len(founders),
    }


def run(seed: int, enhanced: bool, days: int) -> dict:
    sim, _, tree_id = bootstrap(seed=seed)
    tree = sim.world_trees.worlds[tree_id]
    tree.enable_provisioning()
    sim.founder_harvest_enabled = True
    sim.founder_nutrition_enabled = True
    if enhanced:
        sim.founder_tree_independence_enabled = True
        sim.founder_community_foraging_enabled = True
        sim.founder_parent_stewardship_enabled = True
        sim.founder_exchange_enabled = True
        sim.founder_autonomy_learning_enabled = True
    founder_ids = set(sim.founders.people)
    _audit(sim, founder_ids, tree)
    snapshots = []
    copy_at_30 = None
    for day in range(1, days + 1):
        sim.step()
        if copy_at_30 is not None and day <= 35:
            copy_at_30.step()
        if day == 30:
            copy_at_30 = pickle.loads(pickle.dumps(sim))
        if day == 35 and copy_at_30 is not None:
            other = copy_at_30.world_trees.worlds[tree_id]
            if (sim.book.seq != copy_at_30.book.seq
                    or dict(sim.book.mass) != dict(copy_at_30.book.mass)
                    or dict(sim.book.energy) != dict(copy_at_30.book.energy)
                    or tree.provisioning.lots != other.provisioning.lots
                    or set(copy_at_30.founders.people) != founder_ids):
                raise AssertionError("G2 deterministic checkpoint replay mismatch")
        if day in (30, days):
            snapshots.append(_snapshot(sim, tree, day))
    return {
        "gate": "G2-candidate",
        "seed": seed,
        "arm": "g2-voluntary-agency" if enhanced else "g1-funded-baseline",
        "days": days,
        "checkpoint_replay": "PASS" if days >= 35 else "NOT_RUN",
        "snapshots": snapshots,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=4)
    p.add_argument("--days", type=int, default=180)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    if not 1 <= args.seeds <= len(SEEDS) or args.days < 35:
        p.error("seeds must be 1..10, days >= 35")
    rows = []
    try:
        for seed in SEEDS[:args.seeds]:
            for enhanced in (False, True):
                result = run(seed, enhanced, args.days)
                rows.append(result)
                print(json.dumps({"decision": "PASS", **result}, sort_keys=True), flush=True)
    except Exception as exc:
        print(json.dumps({"gate": "G2-candidate", "decision": "FAIL",
                          "seed": seed, "arm": enhanced,
                          "error": repr(exc)}), flush=True)
        raise
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            "\n".join(json.dumps(x, sort_keys=True) for x in rows) + "\n",
            encoding="utf-8")
    print(json.dumps({"gate": "G2-candidate", "decision": "PASS",
                      "matched_seeds": args.seeds, "arms": 2,
                      "runs": len(rows), "horizons": [30, args.days],
                      "ecological_stability": "NOT_INFERRED"}), flush=True)


if __name__ == "__main__":
    main()
