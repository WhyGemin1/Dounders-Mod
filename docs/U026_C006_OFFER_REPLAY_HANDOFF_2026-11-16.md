# U026 C006 — Founder offer replay after settlement (2026-11-16)

## I. Baseline / causal design
- Repository WhyGemin1/Dounders-Mod; Development implementation; Core, Integration and Outer stay unchanged. Development is 177 commits ahead of Core after this cycle; main remains separate.
- C005 introduced safe rejection of ambiguous cross-World lot origin. The next confirmed behavioral defect was in founder_exchange.offer_resource: an already-accepted offer could not replay after the seller spent the lot or the parties separated, because live ownership/contact was checked before the existing offer ID.
- Hypothesis: resolving identical offer identity first allows exact replay without creating a second offer, Book operation, event or source transfer. Alternative: enforce contact on all calls, but that breaks idempotent distributed retry after a valid settlement.
- Falsifier: a settled identical decision replay changes Book/events, is refused for absent current lot/contact, or a conflicting decision is accepted.

## II. Actual implementation
- Source commit 68cbf5cdf52d218e6c9d41c0b49d1d42098d23ff: move existing offer identity and payload conflict checks before new-offer contact/ownership preflight; preserve the original validation for genuinely new offers.
- Test commit 9324c601c8e49a618493ee021b25cb6c0a296980: add test_offer_identity_replay_after_settlement_and_separation_is_side_effect_free to tests/test_c020_resource_agreements.py. Test uses actual bootstrap and Book, confirms stable ID, no extra Book balances/sequence/events/offers, rejects conflicting replay, rejects new remote offer, audits conservation and 100 Founder identities.
- Exact-source candidate manifest commit 0435eb3ee9ddc8ebc2087a68334f65e3d691ba9a: update the two touched paths in docs/U026_G2_CANDIDATE_SOURCE_FINGERPRINT.json; 515 entries preserved. SHA-256 algorithm validated against standard abc vector. Source SHA256 d21de084cd0525e17f6e40eeb1213238fbb9cd17ae1b8e5b61eea4c573fca624; test SHA256 567af5b6eee5ab782693e3bfdc1410778d01eb445c78c29122a91c971a7f54fe.
- Rollback: revert manifest, test and source commits in reverse order after reviewing branch ancestry. No force push.

## III. Tests and RUN_MANIFEST
- Exact source SHA: 0435eb3ee9ddc8ebc2087a68334f65e3d691ba9a.
- Source SHA-256 calculation self-test: PASS; GitHub source/test/manifest writes: SUCCESS.
- Focused pytest: NOT_RUN; full Core151 pytest: NOT_RUN; deterministic checkpoint/replay: NOT_RUN; matched seeds: NOT_RUN; horizons: NOT_RUN; conservation in executable run: NOT_RUN.
- GitHub PR-triggered workflow run for source/test commit 9324c601c8e49a618493ee021b25cb6c0a296980: 43828001215 U026 Core151 integration and 43828001158 WorldBox offline, both in_progress at inspection. Manifest commit 0435eb3e had no PR-triggered run returned at inspection. Do not attribute older CI to current candidate.
- Reproduction: from Founders_CIV_CoreCompletion151/source/world023024, run PYTHONPATH=. python -m pytest -q tests/test_c020_resource_agreements.py and PYTHONPATH=. python -m pytest -q tests; then run exact-source audit and matched seed 820/821/822 control/treatment 30/180 days with Book audits and checkpoint replay. Capture raw outputs before promotion.

## IV. Decision
REVISE / DO NOT PROMOTE. This is an implemented idempotent offer-identity correction, not demonstrated ecological improvement. Real simulation/CI acceptance and source provenance remain pending. Existing G0/G1 historical acceptance is not approval for this source revision. G2/G3/G4 and WB-PKG remain unpromoted.

## V. Branch reconciliation / next cycle
- Development: three confirmed implementation/test/fingerprint commits, plus this documentation handoff.
- Core: no changes, require full green exact-source CI and review; PR #3 stays draft.
- Integration: no changes, later combined Core/Outer adapter testing, two-World identity/replay and matched controls.
- Outer: no changes; WB-PKG Windows compilation/version SHA/hook tests, safe disable, backups, rollback and copied-save user logs remain mandatory before any native gameplay test.
- main: no experimental push.
- Next assignment: verify CI at the exact manifest SHA; resolve any failed test, then implement globally unique World-qualified lot IDs across minting, holdings, ingestion, Book receipts and checkpoint migration, with two actual Worlds and tests. Preserve one Book, chemical vs finite CE, real optional agency, 100 Founders, and genuine ecological failure. Queue G3 scheduler/metabolism, G4 recruitment, P1-09 native read-only event identity, P1-10 two Worlds, P2-11 native gameplay behind WB-PKG, P2-12 CIV-OS research.
