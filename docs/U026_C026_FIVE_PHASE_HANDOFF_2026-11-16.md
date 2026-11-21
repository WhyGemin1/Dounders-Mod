# U026-C026 five-phase handoff — archived clock and historical provenance regressions

Decision: REVISE. Development-only, no Core promotion.

## I Baseline
Live branch comparison before changes: Development 225 ahead/0 behind Core, Integration and Outer (all c935c9a7066d6fe8d122a46edd2d8ce223343be2); 225 ahead/1 behind main (26a02ba50a53770b14eae0368315ea01036d0b3c). C025 CI run 44010028962: core151-python FAILED (313 passed, 2 failed), g1-matched and worldbox-source-offline succeeded. Two failures were stale historical-provenance test expectations: C018 expected world_trees.py approved despite later drift; C004 expected no world_trees.py unapproved drift. Historical approvals MUST remain immutable and fail closed.

## II Implementation
- 48bd0bfd6a6bd2b3ed23e201a0bafd67f730934b: real WORLD-024 archived Tree step increments measured age even without optional provisioning; no fuel or resource production.
- 15ac093553ee796d114c0de3f95533044ee5ad45: regression for seven unprovisioned archived steps, stable Founder identities and Book audit.
- 579a46b3a0da4550c1ad4689c4acd31b1201c9e4: historical C018 attestation now explicitly requires changed Tree source to be unapproved.
- 7bfe822552fd74452540eab937ed45de53ddf6c3: historical C004 approval must also reject current Tree drift. Historical manifests themselves were not rewritten.

## III Verification
C025 run 44010028962 raw GitHub job log confirms 313 passed, 2 failed, and a failed provenance gate; these are NOT C026 test results. New C026 regression and fixes were committed but current-source tests not yet confirmed. G2 516-file exact-source manifest needs new fingerprints for four changed files. No ecological matched seeds or replay experiments executed in this cycle. Run manifest: seed=null, arm=null, horizon=null, resource_audit=not_run, current_source_ci=pending, baseline_ci=failed.

## IV Decision
REVISE. Code fixes clock semantics and corrects stale test expectations without blessing historical source drift. No ecological improvement or acceptance claim.

## V Reconciliation
Only Development was written. Core, Integration, Outer and main untouched. Draft PR #3 remains unmerged. Revert the four commits in reverse order if tests fail after reviewing subsequent ancestry; no force push. Do not promote until exact-source fingerprints, negative tamper, all regressions, conservation, checkpoint and cross-system acceptance pass.

## Next
Reconcile exact four-file SHA256 fingerprints and run current-source CI, inspect failures. Then implement independent two-World scheduler and globally qualified resource ownership through the one Book. Keep WB-PKG gate and native WorldBox gameplay deferred.
