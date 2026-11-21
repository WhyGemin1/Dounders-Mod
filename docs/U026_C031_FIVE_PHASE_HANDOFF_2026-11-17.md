# U026-C031 five-phase handoff — 2026-11-17

Decision: REVISE. G2 exact-source candidate fingerprint reconciliation only; no new engine behavior or promotion.

## I Baseline
Fresh GitHub Core...Development compare: 242 ahead, 0 behind before this cycle. Core c935c9a7066d6fe8d122a46edd2d8ce223343be2. C029 CI run 44038762952: full Python suite and focused tests passed but provenance failed. C030 handoff explicitly identified five drifted files. Hypothesis: reconciling the five exact byte fingerprints will restore clean-source audit while retaining negative-tamper rejection. Falsifier: audit still reports changed/unlisted/forbidden files or mutation is accepted.

## II Change
Existing candidate manifest docs/U026_G2_CANDIDATE_SOURCE_FINGERPRINT.json updated in Development commit 823a89e4b838ae619bde2d00a17d27a33a480053; five SHA-256 entries only, 516-file count preserved. Hashes computed over fresh GitHub UTF-8 contents using a SHA-256 implementation checked against the standard abc test vector. Changed:
- autonomous_provisioning.py c60eeb6209f8ea7e85f57177bb93940f633e4384956bfc53db16331f6b1d5a5c
- world_trees.py 2d0d373ec417d8a7da2ee8b995c924b3b9fb1ee26997dcf1273bcf1c867d3325
- test_autonomous_provisioning_c003.py 4a33228d46edec5af1fb27be08b9eee32a9caacd19aff4f6831532d6f2f419b9
- test_c002_provenance.py bfa711f421483b3b23b55731c99fd11faefe55fdaf8482069d9d733cc0e18fd6
- test_integration_025.py 7ea98810db56fb47b9d49767d9740604d0f9e7dec516adbca246d1729a572324

## III RUN_MANIFEST
Source: GitHub Development at 823a89e4b838ae619bde2d00a17d27a33a480053. Arm: provenance reconciliation. Seeds: none. Horizon: none. New test execution: none. No resource audit, replay, ecology, or native gameplay claimed. Local git checkout blocked by DNS. Run `python tools/u026_g2_exact_source_audit.py`, negative-tamper workflow, `python -m pytest -q tests` in WORLD-024 source, G1 matched tests, checkpoint replay and conservation before promotion.

## IV Decision
REVISE. Manifest reconciliation is verified as a GitHub write, not an executable mechanics improvement. Historical 319 Python passes are not current-source acceptance. No ecological benefit established.

## V Reconciliation
Development-only write succeeded; no Core, Integration, Outer or main merge. Draft PR #3 remains unmerged. Rollback only after review: `git revert 823a89e4b838ae619bde2d00a17d27a33a480053`. Next priority: obtain clean CI including fail-closed mutation controls, then implement two independently advancing Worlds with one authoritative Book, qualified Tree accounts, deterministic replay, and Founder resource use. Keep P1-09 WorldBox event identity, P1-10 two Worlds, P2-11 gameplay integration, P2-12 CIV-OS queued. WB-PKG remains mandatory before copied-save live tests.
