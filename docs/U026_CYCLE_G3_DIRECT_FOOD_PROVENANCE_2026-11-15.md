# U026 CYCLE — G3 direct Book-food nutrition provenance (2026-11-15)

## I Baseline / causal design
Development has a single Core151 Book, opt-in C002 direct TreeResourceOps food and C003 automatic Tree provisioning, and C020 voluntary resource exchange. `founder_exchange._origin` accepts both automatic provisioned lots and Book-created direct food receipts (`food:make:<tree>:<lot>`). G3 nutrition's private `_tree_for_lot` accepted only C003 provisioned lots, so the same physically created food could be traded yet not resolved for ingestion/digestion. Hypothesis: reuse shared source provenance for nutrition. Falsifier: any forged lot or fruit-only receipt resolves as food; any previously valid C003 lot loses resolution; Book changes during lookup. Control: existing C015/C020 integration tests.

## II Actual source change
- `Founders_CIV_CoreCompletion151/source/world023024/founders_civ/core/founder_nutrition.py`: replace duplicate C003-only resolver with `founder_exchange._origin(sim, 'food', lot)`, which already checks Tree provenance and Book operations. No new ledger, clock, fuel, actor controller, CE, or native WorldBox changes.
- `Founders_CIV_CoreCompletion151/source/world023024/tests/test_c015_founder_nutrition.py`: add direct Book provenance regression for Tree with no C003 provisioning, missing/forged lot, and fruit-only receipt.
- Source commit `fb7ee4657692eb27c060744431ee67c80a399dcf`; test commit `2757eb9d368c41348ded7503a69c5a8bff1dcc4c`; exact 515-file fingerprint refreshed at `991c9186c4755738af040c3b46c03b61fdbab3f3`.
- Revert by reverting these three commits in reverse order after checking current Development head; never force push or rewrite G0/G1 attestations.

## III Testing and evidence
- Verified real GitHub source/test writes and returned blob SHA; read GitHub CI workflows.
- Local repository checkout unavailable in execution environment (github.com DNS resolution failed). **Do not count a test as run locally**.
- CI triggered by Development pushes, but **latest final-commit results were pending at authoring**. Verify `U026 Core151 provenance and integration` exact run for fingerprint audit, mutation rejection, 15 G1 focused, G2 parent tests, full Core151 suite and 10-seed G1 matched control; also check separate offline WorldBox M01 workflow.
- Test command in GitHub working tree: `cd Founders_CIV_CoreCompletion151/source/world023024 && PYTHONPATH=. python -m pytest -q tests/test_c015_founder_nutrition.py tests/test_c020_resource_agreements.py tests`; from root `python tools/u026_g2_exact_source_audit.py`.
- RUN_MANIFEST: repository WhyGemin1/Dounders-Mod; branch Development; candidate source `2757eb9d368c41348ded7503a69c5a8bff1dcc4c`; fingerprint commit `991c9186c4755738af040c3b46c03b61fdbab3f3`; test seeds **NOT_RUN on this cycle**; horizons **NOT_RUN**; conservation/replay results **NOT_RUN** on candidate; source fingerprint candidate refreshed, independent audit pending. Historical G1 matched seeds must not be misrepresented as new candidate runs.

## IV Decision
**REVISE / NOT PROMOTED** until exact final-source CI, source audit, full regression and matched replay pass. This is a functional G3 interoperability fix, not evidence of ecological stability or improved survival. The new direct-food regression is unit-level origin validation; the existing C015/C020 suite is the integration control. Do not claim complete direct-food ingestion without an end-to-end funded TreeResourceOps test.

## V Branch reconciliation / handoff
Existing branch responsibilities unchanged: Development candidate, Core reviewed mechanics only, Integration approved combined adapter acceptance, Outer WorldBox C#/BepInEx and WB-PKG, main stable. Branch ancestry at audit: Development 166 commits ahead of Core/Integration/Outer and 166 ahead, 1 behind main; Core/Integration/Outer share c935c9a; main 26a02ba. No merges or PR updates made. Review Development→Core PR #3 without merging until exact-source full regression, complete canonical source and reviewed scope. Native WorldBox remains blocked by WB-PKG and real user copied-save logs.

**Next concrete cycle:** check final-commit CI, fix any provenance/regression failures, implement an actual end-to-end C002 direct-created-food harvest→nutrition→digest test with Book conservation, then matched seed controls. Follow G2 and G3 promotion contracts. G4 juvenile prey/refuge, P1-09 identity/epoch, P1-10 two independently advancing Worlds, P2-11 opt-in physical fruit/Creation adapter and P2-12 RSW/CIV-OS remain in queue.
