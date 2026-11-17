# U026-C033 five-phase handoff — 2026-11-17

Decision: REVISE. Executable fail-closed WORLD-024 habitat-rotation guard committed on Development; current-source CI and exact-source provenance pending.

## I Baseline and hypothesis
Fresh comparisons: Development 63c3ab633bf241f74bd16753ac2f77262bc50163, Core/Integration/Outer c935c9a7066d6fe8d122a46edd2d8ce223343be2, main 26a02ba50a53770b14eae0368315ea01036d0b3c. Development 244 ahead of Core, zero behind, main 244 ahead/one behind. C032 reported 320 passing current-source tests and successful provenance; no independent G2 promotion. Hypothesis: empty, duplicate, or malformed habitat rotations can cause a failed allocation after checkpoint mutation. Falsifier: rejection still advances last_age, Book balances, events or lots. Simpler control: valid habitat rotation continues to provision.

## II Executable change
Modified Founders_CIV_CoreCompletion151/source/world023024/founders_civ/core/autonomous_provisioning.py. Before last_age update, validate a nonempty unique collection of nonempty string habitat identifiers. Source commit 099b8cdf552afc2266655d93fd55a1ed7b190426, content Git blob 394d2ba6936a999181e81b8dac81d7c80b12f5fc. Added test_invalid_habitat_rotation_rejects_before_book_mutation in existing tests/test_autonomous_provisioning_c003.py; test commit a4f8ae5771d2f7b21890c027e98dd4bd8b00bfd3, content Git blob 2c20c65a4e0b10ca5907f8dd20bc24f652073412.

## III RUN_MANIFEST
Arm: malformed habitat fail-closed candidate. Seeds: none newly run. Horizon: none. Tests executed this cycle: zero. Current-source provenance manifest now stale for two files, so promotion blocked. Required reproduction: cd Founders_CIV_CoreCompletion151/source/world023024 && python -m pytest -q tests && python ../../../../tools/u026_g2_exact_source_audit.py (adjust audit invocation to repository root). Run negative-tamper, conservation, identity, checkpoint replay and matched seed controls after reconciling exact SHA-256 entries. No fabricated results.

## IV Decision
REVISE. GitHub source writes verified, not passing integration acceptance or ecological improvement. No WorldBox live tests.

## V Branch reconciliation and rollback
Development-only writes. Core, Integration, Outer and main untouched. No merge or force push. Rollback after review: git revert a4f8ae5771d2f7b21890c027e98dd4bd8b00bfd3 099b8cdf552afc2266655d93fd55a1ed7b190426. Next task: reconcile two fingerprints and execute current-source CI; then independently advancing two Worlds under one authoritative Book, Founder consumption/digestion and deterministic replay. Draft PR #3 remains blocked. WB-PKG mandatory before copied-save gameplay. P1-09, P1-10, P2-11, P2-12 remain queued.
