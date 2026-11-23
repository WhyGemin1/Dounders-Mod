# U026-C023 five-phase engineering handoff — 2026-11-16

Decision: REVISE; Development-only exact-source reconciliation. No Core promotion or ecological improvement.

## I Baseline / causal audit
Fresh GitHub compare before C023: Development 215 ahead/0 behind Core, Integration and Outer, all at c935c9a7066d6fe8d122a46edd2d8ce223343be2. Relative to main 26a02ba50a53770b14eae0368315ea01036d0b3c: 215 ahead/1 behind. C022 changed autonomous_provisioning.py and test_c020_resource_agreements.py, leaving the exact-source candidate stale. Hypothesis: recomputing both fingerprints restores compatibility without relaxing fail-closed checks. Falsifier: audit still fails, mutation is accepted, or full source tests regress. Simpler control: unchanged 514 other fingerprints.

## II Implementation
Updated docs/U026_G2_CANDIDATE_SOURCE_FINGERPRINT.json on existing Development, commit c8fc34300b9f8bdc25baaf518f8d0cfb72fa4511, Git blob ad76f9c69ab0ebbbbeda0efa138644f0a3357398.
- autonomous_provisioning.py SHA256 951d6e7024362ed738a954ad5fce0a63fd7081dc0b5a4abc14d072422ddd3ffe
- test_c020_resource_agreements.py SHA256 de2bd7a2bdff1d142afa4b5d159996fe3c67a8a71f0f93c31f153f84b4570e7a
Manifest remains 516 files. SHA-256 implementation validated with the abc known vector. No executable source edit in C023; C022 executable source remains commit 6147295453bb24a0e101ee6333dac97a0976de86. Rollback: reviewed revert of c8fc343, no force push.

## III RUN_MANIFEST
Source: Development, post-manifest c8fc343. New unit/integration tests: NOT RUN. New seeds: none. Arms/horizons: none. Checkpoint replay: NOT RUN. Book conservation: NOT RUN. GitHub Actions pull-request-triggered workflow lookup returned no runs for c8fc343. Local git checkout blocked by github.com DNS resolution. Reproduce from exact GitHub tree: python tools/u026_g2_exact_source_audit.py; cd Founders_CIV_CoreCompletion151/source/world023024 && PYTHONPATH=. python -m pytest -q tests; negative mutation and unlisted-test checks; G1 matched and two-World conservation/replay controls.

## IV Analysis / decision
REVISE. Manifest reconciliation is necessary but not proof of passing provenance or two-World behavior. Preserve one Book, distinct matter/chemical energy/CE, free Founder choice, stable 100 identities, WorldBox native physiology authority. No ecological improvement claim.

## V Branch reconciliation / next assignment
Core, Integration, Outer, main untouched. Draft PR #3 remains unmerged. Next cycle: run exact-source CI and negative tamper tests, then implement actual independently advancing two-World shared-Book scheduler and matched replay acceptance. Do not promote G2/G3 without independent review. Keep G4, P1-09 native read-only epoch reconciliation, P1-10 two Worlds, P2-11 WB-PKG-gated gameplay, P2-12 CIV-OS in queue. Do not commit generated binaries, saves, SQLite, logs or caches.
