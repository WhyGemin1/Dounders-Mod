# U026-C022 five-phase handoff — 2026-11-16

Decision: REVISE. Development-only executable correction, NOT promoted.

## I Baseline and causal design
Fresh branch comparison: Development 212 ahead of Core/Integration/Outer (all base c935c9a7066d6fe8d122a46edd2d8ce223343be2) and 212 ahead/1 behind main (26a02ba50a53770b14eae0368315ea01036d0b3c) before C022. C021 qualified physical lot identities, but the finite river creation-charge reservation still used local Tree ID and age only. Two independently advancing Worlds with identical local Tree IDs could reuse the same Book operation identity. Hypothesis: qualify CE reservation IDs by World while retaining legacy keys for unqualified Trees. Falsifier: equal keys across Worlds, changed legacy key, or failed Book conservation.

## II Implementation
Changed real canonical module Founders_CIV_CoreCompletion151/source/world023024/founders_civ/core/autonomous_provisioning.py to use ce:reserve:{world_id}:{tree.id}:{tree.age} for explicit World IDs; legacy key remains ce:reserve:{tree.id}:{tree.age}. Source commit 6147295453bb24a0e101ee6333dac97a0976de86, blob 7a05b99bc0de3b05949c5c0bf60d5d16c7f344ae.
Added regression test in tests/test_c020_resource_agreements.py asserting two qualified Worlds with same Tree/age have different CE operation keys, distinct fruit lot IDs, and legacy key remains unchanged. Test commit 9efca4710445b5075b8b8624b7b8fd4b13036d4d, blob 5d95be7a68051627ba41b4349195aacd6bd8ea58.

## III RUN_MANIFEST
Source ref: 9efca4710445b5075b8b8624b7b8fd4b13036d4d. New test is a unit fixture, no seed/horizon. Tests were committed, NOT executed or confirmed passing during this cycle. No ecological matched arms or checkpoint replay executed. Exact-source SHA256 manifest must be reconciled before CI acceptance; do not promote on this evidence.

## IV Analysis and decision
REVISE. This prevents a likely idempotency collision in creation-energy reservations, but does not prove independent two-World simulation, stable ecology or conservation. World-qualified physical Tree resource accounts and global scheduling still require integration testing.

## V Branch reconciliation and handoff
No Core/Integration/Outer/main changes or merge. Draft PR #3 remains blocked. Refresh exact-source manifest for the two changed files; run all Python regression, negative provenance tamper, Book conservation, replay and matched two-World tests. Rollback by reverting test commit then source commit after ancestry review; never force push. Keep WorldBox WB-PKG gate and native physiology unchanged. Do not store generated binaries, saves, databases or logs in GitHub.
