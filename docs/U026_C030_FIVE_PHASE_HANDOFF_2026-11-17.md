# U026-C030 five-phase handoff — 2026-11-17

Decision: REVISE. Development-only; G2 provenance and current-source acceptance pending.

## I Baseline and falsifier
C029 prevented World reassignment after lots were issued but accepted a foreign Tree's lot if its World prefix matched. The falsifier is a lot from a different Tree in WORLD-A being accepted by this Tree's provisioning policy. The control is an original same-Tree lot maturing after collapse.

## II Executable implementation
- `Founders_CIV_CoreCompletion151/source/world023024/founders_civ/core/autonomous_provisioning.py`: validate lot prefix using both explicit World identity and exact Tree ID, retaining legacy single-World format. Commit b485f6071fbe4aa5594e596371174cde4290d8c7, blob 37658bef33ada75fcdc4e943aa1562aad46110e7.
- `Founders_CIV_CoreCompletion151/source/world023024/tests/test_autonomous_provisioning_c003.py`: regression injects foreign Tree lot with same World, requires rejection before policy/Book mutation, then restores original lot and verifies maturation. Commit fcfd0c933933353b557f7ebba818aacf2cfbcecc, blob d528d9b9067b090923992c9fb899eda65821252d.
- No changes to native WorldBox animal physiology, main, Core, Integration or Outer.

## III Actual testing / RUN_MANIFEST
Local checkout attempt: `git ls-remote https://github.com/WhyGemin1/Dounders-Mod.git refs/heads/Development` failed: Could not resolve host github.com. No C030 Python tests, checkpoint replay, new seeds, or ecological trials executed. C030 test is COMMITTED, NOT PASSED.
Historical C029 GitHub run 44038762952: core151-python FAILED because G2 source provenance reported five changed files; underlying Python suite 319 passed in 73.74s; exact G1 replay 17 passed; G2 stewardship 12 passed. G1-matched and worldbox-source-offline passed. Run 44038763007 m01-bridge-build passed. These results are historical, not C030 acceptance.
C030 run manifest: source commit fcfd0c933933353b557f7ebba818aacf2cfbcecc; arm regression-only; seeds none; horizon none; source state GitHub Development, not locally runnable; resource audit not executed; blocker source fingerprints and current-source CI.
Reproduce from exact Development checkout: `cd Founders_CIV_CoreCompletion151/source/world023024 && python -m unittest discover -s tests -p test_autonomous_provisioning_c003.py -v`; run full repository CI, exact-source audit, negative tamper test, replay and conservation.

## IV Ecological analysis
No ecological change or multigenerational improvement established. A stricter provenance guard is a transaction-integrity candidate only. REVISE; do not promote.

## V Branch reconciliation and next assignment
Fresh pre-cycle comparison: Development 239 commits ahead / 0 behind Core; Core, Integration, Outer at c935c9a7066d6fe8d122a46edd2d8ce223343be2. Development diverges from main (main contains separate ZIP commit); do not blind merge. Development writes succeeded. PR #3 remains draft.
Reconcile all changed exact-source SHA-256 fingerprints (at least autonomous_provisioning.py, world_trees.py, test_autonomous_provisioning_c003.py, test_c002_provenance.py, test_integration_025.py), run full tests and negative tamper before any Core review. Next implement independently advancing two-World scheduler, one Book, globally unique Tree accounts, deterministic checkpoint and Founder resource consumption. Maintain P1-09 native read-only event reconciliation, P1-10 two Worlds, P2-11 opt-in gameplay, P2-12 RSW/CIV-OS backlog. WB-PKG requires real Windows compile, assembly SHA/hook checks, user copied-save logs, rollback and Integration review before live gameplay.

Rollback: reviewed `git revert fcfd0c933933353b557f7ebba818aacf2cfbcecc b485f6071fbe4aa5594e596371174cde4290d8c7` in reverse chronological order after confirming branch HEAD; never rewrite history.
