# U026 cycle C005 — cross-World lot provenance safety (2026-11-16)

## I — Baseline and falsifier
- Repository: WhyGemin1/Dounders-Mod; branch: Development; PR #3 remains draft and MUST NOT MERGE.
- Prior G0/G1 exact-source acceptances remain historical; neither constitutes Core promotion. Core, Integration and Outer share c935c9a7066d6fe8d122a46edd2d8ce223343be2; main is 26a02ba50a53770b14eae0368315ea01036d0b3c. Development was 170 ahead of Core before this cycle.
- Prior PR merge run 43809296248 (PR synthetic merge SHA 79ecb22a983d2c9d4ce5b210ef3559b9fde80af2) passed 300 Core151 tests, 17 G1 replay tests, 12 G2 parent-stewardship tests, G1 matched and offline WorldBox tests, but FAILED exact-source provenance because the PR merge contained two G2 stewardship files differing from the manifest. That is **not** a failure of those tests and not an approval to bypass provenance.
- Mechanism: resource lot IDs are used in portable holdings and digestion without a World namespace. The existing shared provenance resolver returned the first World whose Tree had the same lot ID. With two independent Worlds producing the same lot string, one World's resource could be attributed to the other, even when both were Book-backed.
- Falsifier: duplicate World-local lot IDs must resolve as ambiguous (None,None), whereas a single unique origin still resolves. No Book operation, energy, actor identity, or native WorldBox physiology may change during a lookup.

## II — Actual implementation
- Development source commit aefd266e2072e055123ac7b0ceff3d745e6440e1: modify founders_civ/core/founder_exchange.py::_origin to scan all Worlds and reject ambiguous provenance instead of silently choosing lexicographic first.
- Development test commit 2a23043efe34415b28f9e79d20bd1bdc0a61997f: add test_two_worlds_cannot_claim_same_ambiguous_physical_lot to tests/test_c020_resource_agreements.py. The test asserts ambiguous food rejection by both trade and nutrition, fruit unaffected by food-only collision, and successful unique-origin lookup after removing the second provenance receipt.
- Development manifest commit 2de0c31c64cbca235450c5b83d0d178cb1357c65: refresh exactly these two entries in the 515-entry G2 candidate SHA-256 fingerprint manifest.
- Source SHA256: f68b3df8676bc1acb2727adaad8092d9f2533a5b082dc3894a82c3a6d9022d88.
- Test SHA256: 3d3295646efc20f1d2411904cb08068b57d001bbbe438bb9902e72c1d9758d12.
- Revert independently by reverting the two implementation/test commits and manifest commit after confirming branch ancestry; do not force push.

## III — Testing and run manifest
- SHA-256 routine self-test against the published abc digest: PASS; 515-entry manifest updated by code and GitHub update confirmed.
- Current-source pytest: NOT_RUN (GitHub runner status not yet established at this source revision; no local repository checkout because container cannot resolve github.com).
- Current-source deterministic replay: NOT_RUN; matched control/treatment seeds: NOT_RUN; horizons: NOT_RUN; ecological conservation: NOT_RUN.
- Historical PR run 43809296248: 300/300 full tests, 17/17 G1 replay, 12/12 G2 stewardship; FAIL provenance on older PR merge. These results do not verify this change.
- Planned run manifest: exact current Development commit; arms control/new resolver; cases one World, two Worlds unique IDs, two Worlds duplicate IDs; matched seeds 820/821/822 and 30/180 days only after unit, replay, source and conservation checks pass.

## IV — Ecological analysis and decision
**REVISE / DO NOT PROMOTE.** This is a cross-World ownership/identity correctness fix, not evidence of improved populations, juvenile survival or Tree viability. The change deliberately rejects an ambiguous lot rather than guessing; longer-term resolution requires globally namespaced lot identities at minting and through Book receipt/holdings/checkpoint, with backward-compatible migration. Failing safely is preferable to cross-World misattribution.
No G2/G3/G4 or native WorldBox promotion is claimed.

## V — Branch reconciliation and handoff
- Development: code and test committed, source manifest refreshed. GitHub write: SUCCESS.
- Core: no changes; requires reviewed complete canonical source and green exact-source CI.
- Integration: no changes; must later test combined Core plus approved Outer adapter, identity, replay and paired seeds.
- Outer: no changes; WB-PKG Windows compiled DLL, exact assembly version/SHA, hooks, backups, rollback and copied-save user logs remain mandatory before live gameplay.
- main: unchanged; stable release only.
- PR #3: open DRAFT; do not merge. A green test suite without provenance success does not pass the gate.
- Next concrete task: verify GitHub Actions for exact current Development commit; fix any source audit or test failure; then implement globally unique lot IDs across two independent Worlds and a checkpoint-safe legacy identity migration, with actual Book-funded 2-World fixture and tests. Preserve one Book, 100 Founder IDs, finite CE, chemical-vs-CE separation, optional action, and real failure possibilities.
- Pending queue: P0-04 one scheduler/digestion/rest; P0-05 offline WorldBox observer; P0-06 combined regression; P1-07 juvenile recruitment/migration; P1-08 voluntary stewardship; P1-09 native identity/read-only event epochs; P1-10 two independently advancing Worlds; P2-11 opt-in native visualization/pickup/seed integration gated by WB-PKG; P2-12 RSW/CIV-OS research.
