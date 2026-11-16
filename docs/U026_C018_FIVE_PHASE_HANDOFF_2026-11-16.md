# U026-C018 — Authoritative Book harvest isolation (2026-11-16)

Decision: **REVISE**. No promotion. This is a functional safety correction, not the complete two-World identity migration.

## I — Baseline / causal design
Fresh GitHub ancestry comparison: Development was 200 ahead / 0 behind Core, Integration, Outer; 200 ahead / 1 behind main. Core/Integration/Outer base c935c9a7066d6fe8d122a46edd2d8ce223343be2; main base 26a02ba50a53770b14eae0368315ea01036d0b3c. The C016 Core151 workflow passed 308 tests and exact-source provenance. C002/C003/C004 historical results do not demonstrate ecological improvement.

Hypothesis: if a Tree references a different Book than sim.book, harvest may create a physical transfer outside the authoritative conservation ledger. Falsifier: a detached Tree Book can still harvest or the shared-Book control stops harvesting. Alternative: an identity collision between Worlds, already separately fail-closed by C012. Acceptance: reject before transfers, lot-state changes, or event logs, while preserving normal shared-Book harvesting.

## II — Executable implementation
Existing canonical module `Founders_CIV_CoreCompletion151/source/world023024/founders_civ/core/founder_harvesting.py` now checks `tree.book is sim.book` before any Book transfer, with a ValueError on mismatch. Source commit: `5c0a87e5714ed1884df7f4698566fb4a94f855d8`.

Existing `tests/test_u026_c012_cross_world_harvest.py` gained a negative regression using a detached Tree Book and asserting no ledger, lot or event mutation. Test commit: `8bbd2496df96c4ac52508accd85e7c3e2e0e99ee`.

Candidate exact-source manifest `docs/U026_G2_CANDIDATE_SOURCE_FINGERPRINT.json` updated for exactly these two files without disabling fail-closed checks. Commit: `069d5632be098809b1158db9e0632912f64d76b7`.
SHA256: harvesting `60f171a4080a1ff0c46e763e5b513ca9c328db254bc958831a39f4a45c1953f3`; regression `e65c0f7301d326b84645a548a88e4bbcfa864e59082a755008ddabe70c689686`. Hash routine passed the SHA256('abc') reference vector.

## III — RUN_MANIFEST
Source: Development at `069d5632be098809b1158db9e0632912f64d76b7`; arm: detached Book negative regression versus shared Book control; seed: none (deterministic fixture); horizon: N/A; Founder count: N/A. No local checkout: container DNS cannot resolve github.com. No local test execution. Current CI run `43948599565` was in progress at handoff, so current-source passing regression, negative tamper, replay, conservation and ecological matched seeds **not yet verified**. Historical 308/308 is C016, not C018.

Reproduce: `python tools/u026_g2_exact_source_audit.py`; `cd Founders_CIV_CoreCompletion151/source/world023024 && PYTHONPATH=. python -m pytest -q tests`; run the negative tamper and unlisted-source controls; verify Book audit, checkpoint replay, and paired two-World trials before promotion.

## IV — Ecological analysis / decision
This rejects a potential shadow-ledger harvest. It neither implements globally World-qualified IDs nor proves stable juvenile recruitment, Tree health, predator viability or population growth. **REVISE**. No native WorldBox test.

## V — Branch reconciliation / next assignment
Development-only writes; Core, Integration, Outer, main unchanged; PR #3 stays draft. G0/G1 historical Development acceptance, G2 candidate CI pending, G3 unpromoted, G4 unverified, WB-PKG incomplete, G5+ blocked. Reviewed rollback: revert the C018 source/test/manifest commits in reverse order after verifying current ancestry; never force push. No ZIP produced in this run.

Next: verify current-source CI, then implement World-qualified lot identities in WORLD-024 production and Book operations with two independently advancing Worlds, Founder harvest/exchange/digestion, deterministic replay, and conservation tests. Maintain P1-09 native actor epochs, P1-10 dual Worlds, P2-11 opt-in WorldBox adapter, and P2-12 CIV-OS research in the queue. No live gameplay until WB-PKG and user Windows copied-save evidence.
