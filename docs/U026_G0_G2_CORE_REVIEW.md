# U026 G0–G2 selective Core promotion review candidate

Source snapshot: Development `d97c2fd928766499a4d72d95eeae9a20d6d96f40`.
Base: Core `c935c9a7066d6fe8d122a46edd2d8ce223343be2`.
This branch is **temporary PR staging**, not a parallel simulation engine.
There is **NO promotion until approved review and passing exact-candidate GitHub checks**.

## Exact release scope
- Copy only the independently testable, committed `world023024` source subtree at Git tree `c70a65a9fdad10eb96e38c6058e7b023da2849b9` (171 tracked files) and G1/G2 matched runners from the tested Development source.
- Audit whole source tree and runners against pinned Git object hashes. Reject an altered working tree or untracked code. Run an adversarial mutation audit in CI.
- Full 329-test Core151 regression; 17 G1 and 12 G2 focused tests; G1 10-seed x 2-arm matched acceptance; G2 4-seed x 2-arm matched acceptance on this extracted candidate.
- No WorldBox game writes; no proprietary DLLs, local SQLite, saves, or generated binaries.
- Embedded optional G3/G4/experimental source is **not automatically promoted**; its dependencies and default-off behavior require explicit review. The gate's passing tests do **not** establish multigenerational ecological stability.
- Do **not** merge old draft PR #3 or serially merge the entire Development branch.

## Baseline acceptance evidence from Development
- G0 source drift rejection + Core151 regression (329 tests): https://github.com/WhyGemin1/Dounders-Mod/actions/runs/44191636330
- G1 replay/conservation (17 tests) + matched control (10 seeds; 20 runs): same workflow
- G2 independent Tree/agency (89 tests; 4 seeds; 8 matched runs, day 30/180 and checkpoint): https://github.com/WhyGemin1/Dounders-Mod/actions/runs/44191635578
- Evidence applies to tested source, not automatically to Core.

## Review requirement and rollback
Check independent PR approval, exact-source CI, conservation, replay, Founder autonomy and Tree-collapse acceptance. Keep Core SHA unchanged until reviewer signs off. Rollback is closing/discarding this temporary branch; never force push Core/Main. After approved promotion, reconcile Integration separately, then main only after release gates.
