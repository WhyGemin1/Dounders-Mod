# U026-C020 five-phase handoff — 2026-11-16

Decision: REVISE. This is a Development-only executable integrity fix, NOT G2 promotion.

## I Baseline / causal design
Development was 204 commits ahead of Core, Integration and Outer, and 204 ahead / 1 behind main. Core/Integration/Outer SHA c935c9a7066d6fe8d122a46edd2d8ce223343be2; main 26a02ba50a53770b14eae0368315ea01036d0b3c; Development pre-change 966b59647df4fbc01870de310371a6bb9741d011.
Hypothesis: an authentic-looking old provenance key in the shared Book must not authorize a resource from a World Tree currently attached to a different Book. Falsifier: detached Tree resolves to an authentic lot, or a properly attached Tree is rejected. Control: same provenance, same World, Tree attached to shared Book.

## II Executable change
- `Founders_CIV_CoreCompletion151/source/world023024/founders_civ/core/founder_exchange.py`: `_origin` now skips Tree instances whose Book is not the authoritative simulation Book. Legacy lightweight test doubles lacking `book` are supported.
- `Founders_CIV_CoreCompletion151/source/world023024/tests/test_c020_resource_agreements.py`: added paired detached-versus-attached Book provenance regression.
- `docs/U026_G2_CANDIDATE_SOURCE_FINGERPRINT.json`: exact SHA256 entries refreshed.
Source commit b3d6262b96504f69eb8f414d8365ac9e4df81432; test commit 44e3a635c8835ab3195aae5fb2451eb19a0e083e; manifest commit 7ab873c0f49653ba6b66348b060b9776065bb088.
Source SHA256 2355885bf289771f559799762272ae3dc9d957f8ca1d11defdcccaf3619af63a.
Test SHA256 f37c874944e7d550d83987af55d14d046eeb7dab55990d17bb5ee990d3d13880.

## III Testing / run manifest
SHA256 known-vector 'abc' passed. GitHub writes returned confirmed commit SHAs. Current-source Python unit suite, provenance CI, checkpoint replay, conservation and matched-seed ecology NOT run or confirmed during this cycle. No seeds, arms, horizons or ecology improvements claimed. Run manifest: code ref 7ab873c; seeds none; horizons none; Book audit not run; failures not yet determined. The source is unpromoted until CI.

## IV Analysis / decision
Integrity safeguard addresses a detached-Book origin pathway but does not yet introduce globally World-qualified lots or independently advancing two-World economies. REVISE; do not infer population stability.

## V Branch reconciliation / next assignment
No changes to Core, Integration, Outer or main. Do not merge PR #3 without reviewed regression, provenance, replay and conservation acceptance. Rollback by reverting the three commits in reverse order after checking branch ancestry. Next: verify CI; implement truly World-qualified production, harvest, exchange, ingestion and checkpoint identity across two independently advancing Worlds. WB-PKG, read-only native actor epochs, safe gameplay adapter, Windows build and copied-save testing remain gated in Outer. G0/G1 historical Development evidence; G2 pending; G3/G4/WB-PKG/G5+ unpromoted.
