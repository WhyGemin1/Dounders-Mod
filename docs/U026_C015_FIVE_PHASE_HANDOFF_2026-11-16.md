# U026-C015 — exact-source candidate reconciliation (2026-11-16)

Decision: **REVISE**. No promotion. This is a provenance correction, **not** a new executable mechanics implementation. The C014 gate failure was 307/307 Python tests passing but a changed harvesting module and unlisted cross-world test.

## I — Audit and falsifier
Inspected current Development source and candidate manifest, plus Core, Integration, Outer and main ancestry. Hypothesis: listing the missing C012 regression test and hashing actual C012 harvesting source resolves the two reported exact-source failures. Falsifier: current CI still detects mismatches, extra unlisted source, or a mutation control is accepted. Alternative: other drift or merge-checkout differences persist.

## II — Change and rollback
Updated `docs/U026_G2_CANDIDATE_SOURCE_FINGERPRINT.json` on Development, commit `f54a5f76701a6a729b873fb2ad26d1f9d5e05dd4`. The candidate now has 516 entries (previously 515):
- `Founders_CIV_CoreCompletion151/source/world023024/founders_civ/core/founder_harvesting.py`: SHA256 `8f343988cfee48e1b9a3a89d5c8402348da4bcdae1bc6dbac4ffdcba5bde2173`
- `Founders_CIV_CoreCompletion151/source/world023024/tests/test_u026_c012_cross_world_harvest.py`: SHA256 `ff2544cecd7d96dbfff5f2afbc6dbc796cd95e8676afda5e721d71b670577f48`
The SHA256 algorithm was checked against the known SHA256('abc') test vector. GitHub read-back confirmed manifest blob `2996949ff683a8c213971aa8017362285440d95d`. Rollback is a reviewed revert of only commit `f54a5f7`; do not force push.

## III — RUN_MANIFEST
Repo `WhyGemin1/Dounders-Mod`; branch Development; source manifest commit `f54a5f76701a6a729b873fb2ad26d1f9d5e05dd4`; historical source/test revision `d6af7ea3d56f75ece2adf4fddc03d55532734776`. Historical CI `43898887749`: 307/307 Python tests passed, provenance failed with two mismatches. **Current C015 tests: not executed**; no new seeds, arms, horizons, conservation, replay or ecological results. GitHub Actions had no returned PR-triggered runs for the manifest commit at read time. Local checkout unavailable due DNS failure. Reproduce: `python tools/u026_g2_exact_source_audit.py` then `cd Founders_CIV_CoreCompletion151/source/world023024 && PYTHONPATH=. python -m pytest -q tests`; run tamper and unlisted-test negative controls and matched G1 acceptance.

## IV — Ecological decision
REVISE. This does not establish a Tree, Founder, predator, or juvenile survival improvement; G2/G3 are not promoted. Preserve one Book, separate matter/chemical fuel/CE, autonomous Founder decisions, 100 stable identities and native WorldBox authority.

## V — Reconciliation / assignment queue
Development was 195 commits ahead of Core immediately after the manifest commit; Core, Integration and Outer remain at `c935c9a7066d6fe8d122a46edd2d8ce223343be2`; main remains `26a02ba50a53770b14eae0368315ea01036d0b3c`. PR #3 remains draft. No merges. GitHub write succeeded for Development. Next: obtain current-source fail-closed CI acceptance, then implement globally World-qualified food/fruit identities in actual WORLD-024 production and Book paths with cross-World harvest, trade, digestion and checkpoint replay tests. Queue G4 ecology, P1-09 native read-only epoch reconciliation, P1-10 independently advancing two Worlds, P2-11 WB-PKG-gated WorldBox gameplay and P2-12 RSW/CIV-OS.
