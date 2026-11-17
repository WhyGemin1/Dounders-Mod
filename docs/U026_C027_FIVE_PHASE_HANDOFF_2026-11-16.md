# U026-C027 five-phase handoff — fail-closed Tree provisioning Book ownership

Decision: REVISE. Development-only candidate; no Core promotion.

## I Baseline
Fresh GitHub comparisons: Development was 230 ahead/0 behind Core, Integration, Outer (base c935c9a7066d6fe8d122a46edd2d8ce223343be2), and 230 ahead/1 behind main (base 26a02ba50a53770b14eae0368315ea01036d0b3c). C026 handoff reported four outstanding G2 source fingerprints. Source inspection found TreeProvisioningPolicy.tick() did not verify that tree.book is the same object as tree.sim.book before changing last_age or provisioning state.

Hypothesis: a detached Tree Book must fail closed before any state changes. Falsifier: a detached Book causes any policy age, lot, event, or authoritative Book mutation. Control: attached Tree Book retains legacy production.

## II Executable changes
- 36edd2f494eda9c39ab58d4b3108794f0f515b50: source/world023024/founders_civ/core/autonomous_provisioning.py; explicit object-identity guard before last_age mutation.
- 87e1ebfcd0ceca2b1def32dcd6388052c81a7906: source/world023024/tests/test_autonomous_provisioning_c003.py; detached-Book negative test snapshots policy age, lots, events, physical balances and Book sequence, restores attachment and audits.
These paths are relative to Founders_CIV_CoreCompletion151. No replacement simulator, extra ledger, WorldBox native writes or new energy currency.

## III Verification
GitHub returned both commit SHAs and content blob SHAs. No pull-request workflow runs or combined commit statuses were returned for 87e1ebf. Local checkout was attempted and failed DNS resolution for github.com. Therefore tests: NOT RUN; seeds: none; arm: negative regression only; horizon: none; checkpoint: NOT RUN; conservation: test authored but NOT RUN; current G2 fingerprint manifest: STALE (C026 four files plus C027 two files); no claimed passing acceptance.
Reproduction from Development checkout:
`python -m unittest discover -s Founders_CIV_CoreCompletion151/source/world023024/tests -p 'test_autonomous_provisioning_c003.py'`
Then run full Core151 regression, negative tamper audit, checkpoint replay, matched ecological controls, and reconcile exact-source manifest only from verified bytes.

## IV Decision
REVISE. The source change is real and remote, but untested. No evidence of ecological improvement. Detached Book denial must be tested and G2 fingerprint approval must fail closed until reconciled.

## V Reconciliation and rollback
Only Development changed. Core, Integration, Outer, main remain untouched. Draft Development→Core PR #3 must not merge. Review C027 two commits and use normal git revert in reverse order if rejected; no force push. Never deploy WorldBox without WB-PKG.

## Next assignment
1. Reconcile six current source fingerprints including C026 historical changes; run full regression and tamper tests.
2. Implement independent two-World scheduling and shared Book checkpoint replay with World-qualified lot/CE ownership.
3. Retain P1-09 WorldBox read-only identity/event reconciliation, P1-10 two-World, P2-11 opt-in physical gameplay, P2-12 RSW/CIV-OS in queue; WB-PKG incomplete.
