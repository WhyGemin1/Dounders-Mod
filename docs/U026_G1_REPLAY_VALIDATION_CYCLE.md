# U026 G1 — replay payload validation cycle

**Decision: REVISE.** No Core promotion or verified full regression.

## Eight phases
1. Audit: Development ledger contains strict overdraft and exact binary-float replay signatures.
2. Hypothesis: nonfinite and nonpositive quantities must be rejected before idempotent replay lookup.
3. Implementation: commit `f2f7dde40d228eea3527f9a42eadf8dfed6dda2c` validates all material/energy quantities before replay.
4. Adversarial tests: commit `ed712d584712db25e3f516e62462980850b404ab` adds three tests; dedicated file now contains 11 cases.
5. Execution: no confirmed GitHub Actions workflow runs or statuses for test commit. Local container could not resolve github.com to clone source; therefore full suite was not run. No pass count claimed.
6. Ecology: no simulation or matched seeds; no ecology conclusion.
7. Gate: new exact-source attestation, 11 focused tests, full suite, checkpoint and conservation acceptance pending.
8. Branch reconciliation: Development only; Core/Integration/Outer/main not changed.

## RUN_MANIFEST
- repository: WhyGemin1/Dounders-Mod
- branch: Development
- source_commit: ed712d584712db25e3f516e62462980850b404ab
- implementation_commit: f2f7dde40d228eea3527f9a42eadf8dfed6dda2c
- test_path: Founders_CIV_CoreCompletion151/source/world023024/tests/test_u026_g1_exact_replay.py
- tests_added: 3
- tests_in_dedicated_file: 11
- tests_executed: 0
- seeds: []
- horizon_days: []
- source_fingerprint: pending
- decision: REVISE
- rollback: revert only the two G1 commits after checking intervening ancestry; do not force-push
- next: run `cd Founders_CIV_CoreCompletion151/source/world023024 && PYTHONPATH=. python -m pytest -q tests`, inspect failed assertions, run source fingerprint audit, checkpoint replay and matched controls before acceptance.
