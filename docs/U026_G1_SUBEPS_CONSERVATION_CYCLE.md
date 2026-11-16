# U026 G1 — sub-tolerance conservation correction (Development)

Decision: **REVISE — no G1 promotion**. This is a real source correction plus adversarial tests, not a verified full regression.

## Eight-phase record
1. **Audit:** `Book.apply` previously permitted `balance + delta >= -EPS` then clamped negative balances to zero. An empty source transferring `5e-8` units therefore could mint material or energy.
2. **Implement:** `founders_civ/core/ledger.py` now rejects any negative post-transfer balance before mutation; the existing global audit tolerance remains separate from spend authorization. Source commit `bbe2139635acf4c9f6ebc0a84281cf1a87d8a0cb`.
3. **Adversarial tests:** `tests/test_u026_g1_exact_replay.py` adds four tests for empty-source sub-EPS material and chemical energy, exhausted river CE, and a legitimately funded tiny transfer. Test commit `0f2cfd6129817bf22e9426dd68a5dce933de04a9`. Previous four replay tests remain.
4. **Conservation and replay:** new tests assert no state mutation, no operation claim after failure, Book audit, and exact successful transfer; checkpoint/resume still requires independent execution.
5. **Full regression:** PENDING. No successful Actions run or full pytest evidence was available at authoring time. Run from repository root: `cd Founders_CIV_CoreCompletion151/source/world023024 && PYTHONPATH=. python -m pytest -q tests`.
6. **Matched ecology:** NOT RUN; no ecological stability claim. Seed/horizon/arm: null.
7. **Gate review:** New exact-source fingerprints and full CI required; historical G0 acceptance cannot attest these edits.
8. **Branch reconciliation:** Development only. Core/Integration/Outer/main unchanged by this cycle. Do not merge all Development commits blindly.

## RUN_MANIFEST
- branch: Development
- source_commit: 0f2cfd6129817bf22e9426dd68a5dce933de04a9
- implementation_commit: bbe2139635acf4c9f6ebc0a84281cf1a87d8a0cb
- source: Founders_CIV_CoreCompletion151/source/world023024/founders_civ/core/ledger.py
- test: Founders_CIV_CoreCompletion151/source/world023024/tests/test_u026_g1_exact_replay.py
- tests_added: 4
- tests_executed_in_cycle: 0
- CI: not confirmed
- seed: null
- horizon_days: null
- founders_simulated: null
- Book audit results: not yet executed
- decision: REVISE
- next: run CI and exact-source provenance, fix any floating-point regressions, test checkpoint serialization, then review G1-scope promotion.

## Rollback
Revert only the two new commits in reverse order after reviewing intervening commits, or restore the two files from the parent of `bbe2139`; do not force-push or roll back unrelated changes.
