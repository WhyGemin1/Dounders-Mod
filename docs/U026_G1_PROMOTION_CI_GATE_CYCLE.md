# U026 G1 eight-phase promotion attempt — CI enforcement

Decision: **REVISE / PROMOTION BLOCKED**. Do not misrepresent a CI configuration commit as a passing CI run.

1. Baseline: G0 historical accepted commit f604b9d42b5c1547924d9c1346a4ea8668ded208 (241 tests and 497-file audit); subsequent G1 changes invalidate exact-source acceptance.
2. Failure hypothesis: G1 correctness fixes had 11 committed focused tests but no independently verified execution.
3. Implementation: .github/workflows/u026_core151.yml now runs `python -m pytest -q tests/test_u026_g1_exact_replay.py` before `python -m pytest -q tests`. Commit c18866ff726722fc347383772b97bd18868be347.
4. Tests: no verified pass/fail evidence from current workflow. Current environment cannot clone GitHub due DNS; do not invent raw output.
5. Checkpoint and Tree-to-Founder: integration acceptance still pending; do not introduce untested ledger duplication or manual resource edits.
6. Ecology: no matched-seed simulations, no ecological claims.
7. Promotion: require GitHub Actions successful exact commit, new approved 497-file source attestation, 11 focused tests, full regression, checkpoint/replay, Book conservation, Tree lot ownership/ingest, independent review. Preserve historical G0 records.
8. Handoff: Development only, no Core/Integration/Outer/main merge. Do not merge unrelated Development commits.

RUN_MANIFEST: { "gate": "G1", "branch": "Development", "ci_commit": "c18866ff726722fc347383772b97bd18868be347", "focused_tests_expected": 11, "focused_tests_verified": null, "full_suite_verified": null, "matched_seeds": [], "checkpoint_verified": false, "source_attestation_approved": false, "decision": "REVISE" }

Next action: inspect push-triggered Actions on Development for c18866f; retrieve job logs, fix actual failures, regenerate exact-source fingerprint, and rerun. Only then decide whether to promote G1. Rollback CI change via ordinary reviewed revert; no force push.
