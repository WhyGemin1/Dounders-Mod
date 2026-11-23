# U026-C010 — Five-phase provenance reconciliation (2026-11-16)

Decision: **REVISE**, no Core promotion. Exact source gate repaired in Development candidate manifest; fresh CI acceptance not yet verified.

## I — Audit and causal hypothesis
Read actual Development PR #3 HEAD `f31bfe66c8b119c8a9c13995ea7637976c9447a2`, current Core/Integration/Outer/main ancestry, G2 exact-source audit and GitHub Actions run 43858486932. That run executed 305/305 full Core151 tests, 17/17 focused G1 replay tests, 12/12 parent-stewardship tests, and G1 matched acceptance; Core151 job failed because the fail-closed fingerprint check correctly detected four changed files. Hypothesis: correcting the candidate's four hashes to actual reviewed Development bytes allows clean-source audit to pass while still rejecting unauthorized mutations. Alternative: an additional unlisted/mismatched file or PR merge-checkout drift will continue to fail. Falsifier: a clean checkout still reports changed/missing/unlisted files, or mutation/unlisted probes pass undetected.

## II — Implementation
Updated only `docs/U026_G2_CANDIDATE_SOURCE_FINGERPRINT.json` on Development, commit `b7dff17dd604d872b6634155e83b145125ac1a73`. SHA-256 implementation was self-tested against SHA256('abc') and exact current remote file contents fetched from GitHub. Four entries reconciled:
- `founders_civ/core/founder_exchange.py`: `a8acfed70da51508aff5bba505823c4bbc06b96f2116ac16493ab049f2f585e1`
- `founders_civ/core/founder_parent_stewardship.py`: `8181f1c9c3abb630e21374e60a9299e0263da9ca5ef2f49d443281a79597bf18`
- `tests/test_c020_resource_agreements.py`: `47d78a0668078a58d03cf3bb1d79e2de2ceade1913c74f6fc52ba2e16d500746`
- `tests/test_u026_g2_parent_stewardship.py`: `461bcaceca6e7d1e5c816a42a7fafee028f00ce500957fb416a03626236386f3`
Manifest `source_commit` now points to audited source revision `f31bfe66c8b119c8a9c13995ea7637976c9447a2`. No physics, Book, WorldBox or Founder actor logic changed this cycle. This is a gate-unblocking source integrity correction, not a mechanics implementation.

## III — RUN_MANIFEST
Repository `WhyGemin1/Dounders-Mod`; branch `Development`; manifest commit `b7dff17dd604d872b6634155e83b145125ac1a73`; source commit `f31bfe66c8b119c8a9c13995ea7637976c9447a2`; test source `GitHub Actions 43858486932` (historical, before manifest repair).
Historical results: 305/305 full Core151, 17/17 G1 focused, 12/12 G2 focused; CI core151 job failed provenance; matched G1 and offline WorldBox jobs succeeded. Current C010: no completed CI, no new seed/horizon run, no new Book conservation or checkpoint execution. The four candidate hashes were recomputed, but a full 515-file checkout audit has NOT been executed for the new manifest.
Reproduce:
```sh
python tools/u026_g2_exact_source_audit.py
cd Founders_CIV_CoreCompletion151/source/world023024
PYTHONPATH=. python -m pytest -q tests
```
Then run mutation and unlisted-Python negative controls, G1 matched acceptance, replay/conservation and 30/180/360/720/1080-day ecological arms as resources permit.

## IV — Decision
REVISE. The last known CI failure is explained by stale source fingerprints, not failed Python regressions. Candidate hashes are corrected but fail-closed acceptance is not yet demonstrated at C010 revision. No ecological improvement, G2/G3 promotion, or native WorldBox load is claimed.

## V — Reconciliation and next assignment
After manifest commit Development was 189 ahead, zero behind Core, Integration and Outer; 189 ahead and one behind main. PR #3 remains draft, unmerged. No changes to Core/Integration/Outer/main. Preserve one Book, 100 Founder IDs, separate embodied chemical energy/physical matter/Creation Energy, and native WorldBox authority.
Next: confirm CI on current manifest revision, resolve any PR merge-checkout fingerprint mismatch, then implement World-qualified lot IDs across Tree generation, harvest, trade, ingestion, digestion and checkpoint replay. Keep P1-09 native actor epoch reconciliation, P1-10 independent two-World simulation, P2-11 WB-PKG-gated gameplay, P2-12 CIV-OS in queue.
