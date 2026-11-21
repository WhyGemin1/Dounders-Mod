# U026-C025 five-phase handoff — scheduled archived-Tree remnant aging

Decision: REVISE; Development only; no Core promotion.

## I — Baseline
Fresh Development SHA before work: b01bc54ca6b2fac2b0ee0d84c0896c1beb9a3522.
Core/Integration/Outer: c935c9a7066d6fe8d122a46edd2d8ce223343be2.
main: 26a02ba50a53770b14eae0368315ea01036d0b3c.
C024 only refreshed remnant lots when policy.tick() was called manually. Actual WORLD-024 Tree.step() returned immediately for archived Trees. Hypothesis: advancing archived Tree age and policy through the real scheduler restores finite maturation/decay without restarting living ecology. Falsifier: no maturation under sim.step(), new growth after collapse, duplicate events, or Book conservation failure. Control: existing active-Tree and legacy opt-out tests.

## II — Executable implementation
- Founders_CIV_CoreCompletion151/source/world023024/founders_civ/experimental/world_trees.py: archived Tree branch increments measured age and invokes existing provisioning.tick() when enabled, then returns without living ecology or production.
- Founders_CIV_CoreCompletion151/source/world023024/tests/test_autonomous_provisioning_c003.py: new regression test drives the real sim.step() after collapse; asserts maturation, no new lots, 100 stable Founder identities, Book mass audit and same-age idempotency.
- docs/U026_G2_CANDIDATE_SOURCE_FINGERPRINT.json: SHA-256 updated for exactly those two changed files; all other entries preserved.
Source commit: 892d3b246ca0bf74b8eaa99ce9d9a7df53f79326.
Test commit: 017e82663c08ac768fe49d00a02720a83b1e7995.
Fingerprint commit: 4d33823390330978e090c96d4dab3880c18ad825.
New source SHA256: 8e47c93d66df36adc2e420dec23fc444f03b647290611e9a10bbecb924337f45.
New test SHA256: 80fb5153122a691dfe11eded45b97ef154b7399b248710adf3edef727d29d9f7.

## III — Verification
GitHub content writes returned successful commit SHAs. SHA-256 algorithm passed the standard abc vector. Local git checkout failed because github.com DNS could not resolve in the execution container; therefore no local pytest was executed. GitHub Actions runs 44010028962, 44010028936 and 44010025198 were in progress at inspection; they target the test commit, not the final manifest commit. Historical C024 workflow 44002258507 completed successfully, but is not C025 acceptance.
No new ecological matched-seed, 180+/360+/720+/1080-day, conservation stress or checkpoint-resume experiment was run. Seed: none; arm: none; horizon: none; source state: Development candidate; audit: pending; failures: not measured.

## IV — Decision
REVISE. Code now invokes remnant lifecycle in the real WORLD-024 scheduler; actual test acceptance and complete cross-system replay remain unverified. Do not infer ecological benefit.

## V — Reconciliation and rollback
Development was 224 ahead / 0 behind Core, and 224 ahead / 1 behind main after the three implementation/test/manifest commits. No Core, Integration, Outer or main changes. Draft PR #3 stays unmerged. Revert the three commits in reverse order after reviewing subsequent branch ancestry; do not force push. No secrets, binaries, saves, SQLite or logs added.

## Next task
Confirm exact-source CI at the manifest SHA, negative tamper, checkpoint replay, remnant decay and conservation. Then implement independently advancing two-World scheduler with one authoritative Book, World-qualified lot and CE identities, harvesting, exchange and digestion. G0-G1 historical Development evidence; G2 candidate, not promoted; G3 not promoted; G4 unverified; WB-PKG incomplete; G5+ blocked. WorldBox native gameplay remains prohibited until WB-PKG and user copied-save verification.
