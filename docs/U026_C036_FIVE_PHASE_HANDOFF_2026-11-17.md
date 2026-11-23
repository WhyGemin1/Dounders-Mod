# U026-C036 — five-phase handoff (2026-11-17)

Decision: REVISE; do not promote or merge.

I. Fresh branch comparisons: Development 250 ahead of Core/Integration/Outer (c935c9a7066d6fe8d122a46edd2d8ce223343be2), and 250 ahead / 1 behind main (26a02ba50a53770b14eae0368315ea01036d0b3c) before C036 writes. C035 CI run 44091994293 succeeded: 322 Python tests, G2 exact-source provenance, G1 matched and offline WorldBox source jobs.

II. Existing canonical WORLD-024 source changed: `Founders_CIV_CoreCompletion151/source/world023024/founders_civ/core/autonomous_provisioning.py` now rejects noninteger, boolean and negative Tree ages before checkpoint or Book mutation. Source commit ddaa20374ddc69107b5ff1a88b59d9d78176f335; blob 33e7b6b3065c92bd508258e1deb4c931bd571fc4. Added negative/recovery regression to `Founders_CIV_CoreCompletion151/source/world023024/tests/test_autonomous_provisioning_c003.py` in commit 7f38c182df31289a9e554b8c8e714b53d4150c01, blob 3a26f1ae3726b0f9cd83ea4bbd5a72c07aacb33f. Rollback: review/revert only these two commits in reverse order, without force push. Historical attestations unchanged.

III. C036 current-source CI triggered (GitHub Actions run 44101802872); queued at handoff, not passed. No local full-suite execution because container DNS could not resolve github.com. No new seeds/horizons or ecological claims. G2 candidate manifest needs exact-source SHA256 reconciliation and negative tamper before promotion.

IV. Hypothesis: invalid age checkpoint types must not mutate lot maturity, Book balances, event stream or last_age. Control: valid integer ages continue ordinary provisioning. Falsifier: any invalid-age test mutates state or any normal-age regression fails. No evidence of ecological improvement.

V. Core, Integration, Outer, main untouched. PR #3 remains draft/unmerged. Next: inspect CI and reconcile exact source manifest; test checkpoint replay, conservation, identity and two independently advancing Worlds with one authoritative Book. WB-PKG and live WorldBox remain blocked. Never interpret virtual Worlds as native game worlds.
