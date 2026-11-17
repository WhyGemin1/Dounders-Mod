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
PROFILES = {
    "g1-funded-baseline": (),
    "g2-observe-exchange": ("founder_community_foraging_enabled",
                            "founder_exchange_enabled"),
    "g2-tree-agency": ("founder_tree_independence_enabled",),
    "g2-parent-stewardship": ("founder_parent_stewardship_enabled",),
    "g2-social-learning": ("founder_autonomy_learning_enabled",),
    "g2-voluntary-agency": ("founder_tree_independence_enabled",
                            "founder_community_foraging_enabled",
                            "founder_parent_stewardship_enabled",
                            "founder_exchange_enabled",
                            "founder_autonomy_learning_enabled"),
}


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


def _snapshot(sim, tree, day, founder_ids):
    audit = _audit(sim, founder_ids, tree)
    lots = tree.provisioning.lots if tree.provisioning else {}
    states = {}
    for lot in lots.values():
        states[lot.state] = states.get(lot.state, 0) + 1
    worlds = list(sim.world_trees.worlds.values())
    # An original Tree's collapse is not proof all Worlds died: distinguish
    # original population from ALL actually funded World Tree populations.
    return {
        "day": day,
        "worlds_count": len(worlds),
        "active_worlds": sum(t.state == "active" for t in worlds),
        "total_living_residents": sum(t.population for t in worlds),
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
        "founders": len(founder_ids),
    }


def run(seed: int, enhanced: bool, days: int, profile: str | None = None) -> dict:
    sim, _, tree_id = bootstrap(seed=seed)
    tree = sim.world_trees.worlds[tree_id]
    tree.enable_provisioning()
    sim.founder_harvest_enabled = True
    sim.founder_nutrition_enabled = True
    profile = profile or ("g2-voluntary-agency" if enhanced else "g1-funded-baseline")
    if profile not in PROFILES:
        raise ValueError("unknown G2 factorial profile")
    for flag in PROFILES[profile]:
        setattr(sim, flag, True)
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
            snapshots.append(_snapshot(sim, tree, day, founder_ids))
    return {
        "gate": "G2-candidate",
        "seed": seed,
        "arm": profile,
        "days": days,
        "checkpoint_replay": "PASS" if days >= 35 else "NOT_RUN",
        "snapshots": snapshots,
    }


def paired_collapse_regressions(rows):
    """Flag candidate-only collapse; do not disallow natural failure in both arms."""
    grouped = {}
    for row in rows:
        snap = next(x for x in row["snapshots"] if x["day"] == row["days"])
        grouped.setdefault(row["seed"], {})[row["arm"]] = snap
    failures = []
    for seed, arms in sorted(grouped.items()):
        control, candidate = (arms.get("g1-funded-baseline"),
                              arms.get("g2-voluntary-agency"))
        if control is None or candidate is None:
            failures.append({"seed": seed, "reason": "missing_paired_arm"})
        elif (control["active_worlds"] > 0
              and control["total_living_residents"] > 0
              and candidate["active_worlds"] == 0
              and candidate["total_living_residents"] == 0):
            failures.append({"seed": seed, "reason": "candidate_only_extinction",
                             "control_residents": control["total_living_residents"]})
    return failures


def _test_paired_regression_gate():
    def row(seed, arm, count):
        snap = {"day": 180, "active_worlds": int(count > 0),
                "total_living_residents": count}
        return {"seed": seed, "arm": arm, "days": 180, "snapshots": [snap]}
    rows = [row(42, "g1-funded-baseline", 30),
            row(42, "g2-voluntary-agency", 0)]
    assert paired_collapse_regressions(rows)[0]["reason"] == "candidate_only_extinction"
    rows[1] = row(42, "g2-voluntary-agency", 22)
    assert paired_collapse_regressions(rows) == []
    rows[0] = row(42, "g1-funded-baseline", 0)
    rows[1] = row(42, "g2-voluntary-agency", 0)
    assert paired_collapse_regressions(rows) == []
    assert paired_collapse_regressions(rows[:1])[0]["reason"] == "missing_paired_arm"
    print("G2 paired ecological regression gate negative controls PASS")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=4)
    p.add_argument("--days", type=int, default=180)
    p.add_argument("--output", type=Path)
    p.add_argument("--factorial", action="store_true",
                   help="compare G2 options separately before promoting full agency")
    p.add_argument("--self-test", action="store_true",
                   help="exercise promotion rejection with synthetic matched failures")
    args = p.parse_args()
    if args.self_test:
        _test_paired_regression_gate()
        return
    if not 1 <= args.seeds <= len(SEEDS) or args.days < 35:
        p.error("seeds must be 1..10, days >= 35")
    profiles = tuple(PROFILES) if args.factorial else (
        "g1-funded-baseline", "g2-voluntary-agency")
    rows = []
    profile = "NOT_STARTED"
    try:
        for seed in SEEDS[:args.seeds]:
            for profile in profiles:
                result = run(seed, profile != "g1-funded-baseline",
                             args.days, profile=profile)
                rows.append(result)
                print(json.dumps({"decision": "PASS", **result}, sort_keys=True), flush=True)
    except Exception as exc:
        print(json.dumps({"gate": "G2-candidate", "decision": "FAIL",
                          "seed": seed, "arm": profile,
                          "error": repr(exc)}), flush=True)
        raise
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            "\n".join(json.dumps(x, sort_keys=True) for x in rows) + "\n",
            encoding="utf-8")
    paired_failures = paired_collapse_regressions(rows)
    decision = "FAIL_PAIRED_EXTINCTION" if paired_failures else "PASS"
    print(json.dumps({"gate": "G2-candidate", "decision": decision,
                      "matched_seeds": args.seeds, "arms": len(profiles),
                      "runs": len(rows), "horizons": [30, args.days],
                      "paired_extinction_regressions": paired_failures,
                      "ecological_stability": "NOT_INFERRED"}), flush=True)
    if paired_failures:
        raise SystemExit("G2 promotion blocked: matched candidate-only World Tree extinction")


if __name__ == "__main__":
    main()
