# U026-C029 five-phase handoff (2026-11-17)

Decision: REVISE. Development-only, not promoted.

## I Baseline
C028 accepted malformed namespace rejection before mutation, but valid World reassignment after existing lots remained possible. This can corrupt ownership provenance across independently advancing Worlds. Hypothesis: rejecting reassignment before remnant refresh prevents mixed-origin lots. Falsifier: a Tree with existing WORLD-A lots can advance under WORLD-B without rejection. Control: unchanged WORLD-A can continue aging its archived lots.

## II Implementation
- `Founders_CIV_CoreCompletion151/source/world023024/founders_civ/core/autonomous_provisioning.py`: fail closed if any previously issued lot does not match the current World-qualified (or legacy) prefix, before policy checkpoint changes.
- `Founders_CIV_CoreCompletion151/source/world023024/tests/test_autonomous_provisioning_c003.py`: added negative reassignment and positive recovery test, including Book balances and remnant maturation.
- Commits: source `f970e3808dca2f3f94333564206f43a394adff9d` (blob `8b25e330c376e9dd99578bb6c4828b1032ee4fbd`); test `af8863c6e3b7e2fe95be06e27aecba2a982f9c8a` (blob `ab5f1275fff7f54bf4a9bd7ed5ec7746e3386582`).

## III Testing
GitHub contents API confirmed both writes. No full Python regression, negative tamper suite, checkpoint replay or ecological simulation was executed this cycle: local GitHub DNS checkout failed. Test acceptance is pending. Provenance manifest requires reconciliation. No seeds or horizons executed; do not infer ecological improvement.

Reproduction from Development checkout:
```sh
cd Founders_CIV_CoreCompletion151/source/world023024
python -m unittest discover -s tests -p 'test_autonomous_provisioning_c003.py' -v
```
Then run repository CI and exact-source audit with negative tamper control. Expected new test: World reassignment rejected before Book or policy mutation; restoring original World permits maturation.

## IV Decision
REVISE. The guard preserves origin consistency but does not implement two independent Worlds, and ecological outcomes remain unknown.

## V Reconciliation
Development only. Core, Integration, Outer and main unchanged. No merge/force push. Rollback: revert the two code/test commits with reviewed non-destructive Git reverts; do not rewrite history. PR #3 remains draft pending full-source regression, provenance, checkpoint and acceptance review.

## Next
Reconcile exact-source fingerprints, execute full regression and checkpoint replay, then implement two independently advancing Worlds with one Book and explicit globally unique Tree account identities. Retain G0-G4 and WB-PKG gates; no native WorldBox test until complete Windows package and user logs.
