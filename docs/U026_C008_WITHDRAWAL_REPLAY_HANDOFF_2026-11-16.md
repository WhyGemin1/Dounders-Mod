# U026-C008 five-phase handoff — 2026-11-16

Decision: **REVISE**, no Core promotion. Assignment: G2/G3 Book-backed voluntary agreement replay after seller death.

## I — Audit / causal hypothesis
Current Development source in `founders_civ/core/founder_exchange.py` handled accepted/declined decisions after recipient death, but `withdraw_offer` rejected a previously withdrawn offer after seller death because the live-actor guard preceded the historical withdrawn-status check. Control: a *new* withdrawal by a dead seller must still fail. Falsifier: replay changes Book state or logs an event, or permits an open offer to be withdrawn by a dead seller.

## II — Executable implementation
- Source commit `64ddc83cba6d60c4da02ccdad7889bb76881cf00`: historical withdrawn status is checked before current seller activity. Original seller identity remains mandatory.
- Regression commit `d00467a22c3c1413d7f591228d5a0e9ab9e91bbe`: `test_withdrawn_offer_replay_after_seller_death_is_historical_not_new_action`, seeds 824/825 used in fixture setup. Tests check unchanged Book mass/energy/sequence, event count, withdrawn state, no acceptance of withdrawn offer, and rejection of new withdrawal by a dead seller.
- Fingerprint commit `ff5f66b330f45a98694f93f52eee4c6cebf9b5b4`: updated two SHA-256 entries in 515-file candidate manifest; hash routine passed SHA-256 'abc' known-vector self-test. No historical G0 attestation overwritten.
- No WorldBox native writes, no second Book, no new energy or action-time currency.

## III — RUN_MANIFEST (execution truth)
- Source branch: Development; fingerprint commit: `ff5f66b330f45a98694f93f52eee4c6cebf9b5b4`.
- Focused pytest: **NOT EXECUTED**. Full pytest: **NOT EXECUTED**. Matched ecological arms/horizons: **NOT EXECUTED**.
- Reason: local container `git ls-remote` failed DNS resolution of github.com; connector supports file edits but not a runnable checkout. No CI runs were returned for the fingerprint commit at inspection.
- Fixture seeds 824/825 are **test code inputs, not executed simulation results**. Conservation, identity and checkpoint acceptance at this SHA: **UNVERIFIED**.
- Reproduce in an exact GitHub checkout:
  ```sh
  python tools/u026_g2_exact_source_audit.py
  cd Founders_CIV_CoreCompletion151/source/world023024
  PYTHONPATH=. python -m pytest -q tests/test_c020_resource_agreements.py
  PYTHONPATH=. python -m pytest -q tests
  ```
- Then run `python tools/u026_g1_matched_acceptance.py --seeds 10 --days 180` at repo root and record raw logs, commit SHA, seed, arm, horizon, replay and Book audits. Source drift remains fail-closed until a clean checkout audit succeeds.

## IV — Ecological decision
**REVISE**. This is a narrowly scoped historical-idempotency correction, not evidence of improved Tree ecology, juvenile survival, predator recruitment or long-horizon population stability.

## V — Reconciliation / assignment queue
- Development vs Core/Integration/Outer: 184 ahead, 0 behind; each comparison base SHA `c935c9a7066d6fe8d122a46edd2d8ce223343be2`.
- Development vs main: 184 ahead, 1 behind; main base SHA `26a02ba50a53770b14eae0368315ea01036d0b3c`.
- PR #3 remains draft; do not merge. Core, Integration, Outer and main unchanged by C008.
- G0/G1 historical Development acceptance only; G2/G3 unpromoted at current source; G4 unverified; WB-PKG/G5+ blocked.
- Next: obtain current-source CI verdict and repair exact-source failures before further changes. Then implement World-qualified physical lot IDs across Tree generation, harvesting, trade, nutrition and checkpoint replay, using the same Book. Queue P1-09 read-only native identity/epoch reconciliation; P1-10 two independently advancing virtual Worlds; P2-11 opt-in native gameplay after complete WB-PKG, Windows build, hook/version checks, backups, rollback, Integration approval and copied-save user logs. P2-12 RSW/CIV-OS remains backlog.
