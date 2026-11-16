# U026 G1 — eight-phase implementation and promotion cycle

**Status:** planned / not promoted. **Starting gate:** G0 accepted on Development exact source `f604b9d42b5c1547924d9c1346a4ea8668ded208`; documented in `docs/U026_G0_GATE_STATUS.json`. Preserve all historical approvals. G1 requires separately reviewed exact-source attestation and successful CI.

## Gate definition

G1 means **one authoritative Core151 Book** for resource ownership and transfers, with distinct conserved **physical matter**, **embodied chemical energy**, **heat/waste**, and **fictional finite river Creation Energy (CE)**. Real WORLD-024 Tree food and fruit lots must have stable identities; Founder access/harvest/ingest/digest/seed funding must be atomic, replay-safe, checkpoint-safe and fail closed. G1 does **not** certify multigeneration ecology, native WorldBox gameplay, G2–G4, or a Core/main merge.

### Eight phases (implementation-led; no plan-only promotion)

1. **Baseline and ancestry audit.** Read fresh refs for Development, Core, Integration, Outer, main. Inspect `founders_civ/core/ledger.py`, `founders_civ/core/founder_harvesting.py`, `founders_civ/core/founder_nutrition.py`, `founders_civ/core/founder_recovery.py`, `founders_civ/experimental/world_trees.py`, `founders_civ/experimental/world_integration.py`, checkpoint serializers, all source hashes, tests, C002–C038 approvals. Record source SHA and G0 baseline. Identify actual G1 gaps by failing tests before editing.
2. **Atomic Book and typed stock implementation.** On Development implement any demonstrated gap in single-Book `apply` and typed resource APIs: prevalidate full multi-leg transaction, prevent overdraft/negative stock, stable asset IDs, operation-ID replay with conflict rejection, separate CE from chemical fuel and waste/heat. Free proposals; no action permission purchased with time or energy. Add failure-injection tests proving no partial mutation.
3. **Tree-to-Founder-to-World funding integration.** Implement real mature fruit and food lot transfers, observation/riverbank access, owner transitions, paired food+chemical energy ingestion, digestion/rest without fuel mint, and Book-funded world-seed creation. Reject nonexistent, immature, stale, duplicate, double-spent or unauthorized lots. Maintain WORLD-024 Tree failure/collapse/remnant and two-Tree shared finite river CE. No native physiology writes.
4. **Identity and deterministic replay.** Save/restore Book operations, asset tombstones, Founder/Tree IDs, lot ownership, scheduler tick and RNG. Run duplicate ACK/transaction retries, same ID different payload, failed-then-retried transfer, checkpoint at transaction boundaries, and exact replay. Compare canonical state hashes and Book audits.
5. **Focused unit and adversarial integration tests.** Run complete GitHub-working-tree Core151 suite plus tests for typed stock, conservation, rollback, ownership, CE/chemical segregation, duplicate operation IDs, resource maturation/decay and failure injection. Include negative cases and source-mutation rejection; store raw pytest output, commands, environment and source SHA.
6. **Matched simulations and ecological analysis.** Run at least eight control/treatment matched scenarios, with 100 Founders, recorded seeds, 30/180-day horizons and replay, then extend toward 8 arms x 30 seeds and 360/720/1080 days only when feasible. Report population, juvenile survival, predator recruitment, food accessibility, Tree health/collapse, Founder agency, Book mass/energy/CE and rejections. Compare against simpler control; G1 may pass for correctness without claiming ecological improvement.
7. **Independent gate review and decision.** Build exact SHA-256 manifest for all changed tracked source and tests; preserve immutable historical C018/C036/G0 records. Obtain CI success on the same commit, full regression and fail-closed provenance checks. Record `PROMOTE`, `REVISE`, or `REVERT` with falsifiers, residual risk and rollback. Any changed tracked source invalidates prior exact-source acceptance until reverified.
8. **Branch reconciliation and complete handoff.** Keep implementation on Development. Review only G1-scoped diffs before PR to Core; do not merge all unrelated Development commits. Core is authoritative only after reviewed regression-passing merge. Integration separately validates combined Core+approved Outer adapter, replay and conservation. Outer owns WorldBox adapter, WB-PKG, copied-save instructions and rollback. Main remains stable. Deliver code/patch, SHA manifest, RUN_MANIFEST, raw tests, DECISION, DEVLOG, assignment queue, source ZIP and next-cycle handoff.

## Mandatory promotion checks

- **Source:** exact-source SHA fingerprint audit clean (zero missing/changed/forbidden); G0 historical provenance intact.
- **Book:** zero unauthorized minting or negative stock; transaction atomicity; idempotent exact retries; conflicting retries rejected; typed matter/chemical energy/CE not interchangeable.
- **Resources:** real Tree-owned lot IDs and maturity; harvest/ingestion/digestion/seed funding physically and transactionally accounted; decay/collapse conservation; no duplicate lot spending.
- **Replay:** deterministic checkpoint/resume and stable Founder/Tree/lot/transaction identity; repeated actions do not double spend.
- **Tests:** full Core151 suite green from exact GitHub commit, targeted G1 tests, paired-control manifests, raw evidence and reproducible commands.
- **Governance:** independent review and recorded gate decision. G1 acceptance is not proof of ecological stability or native WorldBox deployment.

## Immediate implementation assignment

Audit the current Book resource transaction and checkpoint paths, reproduce a specific G1 correctness failure, fix it in Development with adversarial tests and rollback, and rerun CI. Do not add monitoring alone. Existing G0 pass: [Actions run 43784994919](https://github.com/WhyGemin1/Dounders-Mod/actions/runs/43784994919); promotion-record follow-up [43785239624](https://github.com/WhyGemin1/Dounders-Mod/actions/runs/43785239624). No G1 promotion is asserted here.

## RUN_MANIFEST minimum schema

`{cycle, branch, source_commit, source_manifest_sha256, command, environment, seed, arm, horizon_days, founders, source_state, test_counts, book_audit, transaction_replays, checkpoint_digest, population, juvenile_survival, tree_status, decision, blockers}`

## Gate queue

G0 = verified on Development; G1 = pending separate acceptance; G2/G3/G4 = not promoted; WB-PKG = not verified live; G5+ = not promoted.
