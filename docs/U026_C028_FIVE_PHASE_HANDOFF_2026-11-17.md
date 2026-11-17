# U026-C028 five-phase handoff — fail-closed World namespace validation before remnant refresh

Decision: REVISE. Development-only candidate; no Core/Integration/Outer/main promotion.

## I Baseline and hypothesis
Fresh comparisons on 2026-11-17: Development 233 ahead/0 behind Core, Integration, Outer (all c935c9a7066d6fe8d122a46edd2d8ce223343be2); 233 ahead/1 behind main (26a02ba50a53770b14eae0368315ea01036d0b3c). C027 source and tests read directly from GitHub. The Tree provisioning policy validated world_id only when creating a new lot, after tick() had already changed last_age and refreshed stored lots. Hypothesis: an invalid namespace must fail before even remnant maturation. Falsifier: policy last_age, lot states, events, or Book balances change on rejected input. Control: after clearing invalid world_id, maturation resumes.

## II Executable source
- 305a08f500e88548781cfb69b0cb78dea98a9fd3 changes Founders_CIV_CoreCompletion151/source/world023024/founders_civ/core/autonomous_provisioning.py: validate optional world_id at start of tick(), before last_age or _refresh().
- 02525d20acde09428c232f95fb832350a7b8a91a adds test_invalid_world_namespace_rejects_before_remnant_refresh in source/world023024/tests/test_autonomous_provisioning_c003.py. Test snapshots Book and policy state, rejects malformed ID, clears it, verifies maturation and audits the Book.
- No replacement simulator, extra ledger, native WorldBox write, or new time/energy currency.

## III Verification / RUN_MANIFEST
GitHub source and test update responses returned successful commit and content blob SHAs. Local git ls-remote failed: Could not resolve host github.com. No executable tests were run; seeds none; arms none; horizons none; conservation/checkpoint/replay not executed; ecological comparisons not executed. CI run lookup for C027 returned no PR workflow runs or combined statuses. C028 exact-source provenance manifest is STALE and must fail closed; do not claim acceptance.

Reproduction: python -m unittest discover -s Founders_CIV_CoreCompletion151/source/world023024/tests -p 'test_autonomous_provisioning_c003.py'; then run full Core151 regression, negative tamper, Book conservation, checkpoint/replay, and matched controls from the exact Development SHA. Reconcile all changed SHA-256 source entries from exact bytes only.

## IV Decision
REVISE: concrete mechanics guard implemented, but not test-accepted and no ecological improvement established. The two-World scheduler and qualified Tree account identity remain unresolved.

## V Branch reconciliation and next assignment
Only Development changed. Core, Integration, Outer, main untouched. PR #3 remains draft; no blind merge or force push. Rollback via normal git revert 02525d2 then 305a08f if rejected. Next: reconcile exact-source fingerprints and run full regressions; implement actual two-World scheduling with one authoritative Book, stable 100 Founder IDs, globally qualified physical accounts/CE and deterministic checkpoint. Preserve P1-09 native read-only event reconciliation, P1-10 two Worlds, P2-11 opt-in gameplay, P2-12 research. WB-PKG remains mandatory and incomplete; no live WorldBox gameplay.
