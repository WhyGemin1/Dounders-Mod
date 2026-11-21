# U026 G2 — physical locality guard, five-phase cycle (2026-11-15)

## I. Baseline and causal claim
Development contains the actual Core151/WORLD-024 integration, G0/G1 exact-source accepted historical revisions, and G2 unpromoted candidate. Current observed bug: parent Realm inspection requires a living Founder at house or riverbank, but a subsequent **new** stewardship transfer accepted a remote Founder from ridge while the earlier observation was still fresh. This bypasses physical access despite a real Book-funded transfer. Alternative: remote agreements might legitimately transfer assets, but this action is direct physical tending, not an agreed remote Book transfer. Falsifier: new remote tending succeeds or existing Book receipt replay fails.

## II. Actual source changes
- `Founders_CIV_CoreCompletion151/source/world023024/founders_civ/core/founder_parent_stewardship.py`: after the original Book receipt replay path and before reading current reserve knowledge, reject new tending when `person.location` is not in `OBSERVATION_SITES`. Existing receipts remain idempotently acknowledged even if the Founder has moved.
- `Founders_CIV_CoreCompletion151/source/world023024/tests/test_u026_g2_parent_stewardship.py`: `test_remote_new_stewardship_rejected_but_prior_receipt_replays` verifies rejection, no balance/sequence/event changes, valid prior receipt replay and Book audit.
- `docs/U026_G2_CANDIDATE_SOURCE_FINGERPRINT.json`: updated both exact SHA-256 entries, keeping 515 tracked paths.
- Confirmed GitHub Development commits: source `0d3e5dc0a883a64703824ef8d47309ed529c7562`; test `2ea2f907237a32156b014ad4199983cdc7446f33`; fingerprint `d5175c5339bcdad02238420373d356f70359a2ab`.
- SHA-256 source: `8caf9dfa7255045e23a2829820db45415561f1de2f496d0ea57375284f92a19e`; test: `588d024cbef8b45e7878f4bb8a02447f9fdfc6a55cf2c5a95558d1d3c44f7d61`. Hash implementation checked against published SHA-256 "abc" test vector. Read-back confirmed the two GitHub blobs.

## III. Testing and RUN_MANIFEST
```json
{
  "source_commit": "d5175c5339bcdad02238420373d356f70359a2ab",
  "branch": "Development",
  "changed_python_files": 2,
  "fingerprint_entries": 515,
  "test_command": "cd Founders_CIV_CoreCompletion151/source/world023024 && PYTHONPATH=. python -m pytest -q tests/test_u026_g2_parent_stewardship.py && PYTHONPATH=. python -m pytest -q tests",
  "test_status": "NOT_RUN",
  "reason": "GitHub connector can read/write files but cannot execute shell or dispatch Actions; sandbox cannot resolve github.com and has no checked-out canonical source",
  "github_actions_on_final_commit": [],
  "matched_seeds": [],
  "matched_horizons": [],
  "book_conservation": "NOT_RUN on changed revision",
  "checkpoint_replay": "NOT_RUN on changed revision"
}
```
No new simulation result, CI success, ecological improvement or promotion is claimed. Previously accepted G0/G1 evidence is valid only for its own historical source commits. No release ZIP or full patch package is claimed here.

## IV. Decision
**REVISE (G2 not promoted)**. Source-level physical-access correction and regression are committed, but source fingerprint audit, full Core151 tests and matched simulations have not run at the final SHA. A local physical-access guard is not evidence of long-term ecological improvement.

## V. Branch reconciliation and handoff
GitHub compare at this cycle: Development ahead of Core by 139, ahead of Integration by 139, ahead of Outer by 139; ahead of main by 139 and behind main by 1. Do not merge whole Development or bypass PR review. Development remains implementation branch; Core is promoted mechanics; Integration cross-system verification; Outer offline WorldBox adapter/WB-PKG; main stable release. Native gameplay not tested and WB-PKG not accepted.

**Next unblocked engineering action:** execute the exact-source audit and full CI for Development `d5175c5`, including new locality test and G1 replay/matched jobs. If green, add matched-seed G2 physical-access/Tree-resource tests, inspect PR #3 and promote only reviewed scoped changes. Preserve G4 recruitment and P1-09/P1-10/P2-11 WorldBox queue, including mandatory WB-PKG and user copied-save logs. Do not equate offline World Trees with native game Worlds.
