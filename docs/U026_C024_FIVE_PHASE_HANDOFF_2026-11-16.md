# U026-C024 five-phase handoff — 2026-11-16

Decision: REVISE. Development-only executable correction; tests pending, not promoted.

## I Baseline / causal design
Development was 217 commits ahead / 0 behind Core, Integration and Outer (all c935c9a7066d6fe8d122a46edd2d8ce223343be2), and 217 ahead / 1 behind main (26a02ba50a53770b14eae0368315ea01036d0b3c). Previous C023 source manifest had 516 entries. Existing Tree provisioning returned before refreshing physical lots when a Tree was archived, freezing maturity/decay of its remnants. Hypothesis: refresh before active-state gating permits post-collapse aging while preventing new production. Falsifier: collapse prevents maturation, produces new lots, duplicates events on replay, or breaks Book conservation. Control: existing active Tree provisioning and archived Tree harvest tests.

## II Implementation
On Development:
- ade323a81924474ab3ae763eba9a1df15b421ffd: move _refresh() before active/stable Tree gating in founders_civ/core/autonomous_provisioning.py; still no new production for inactive Trees.
- c774148c19b8f20b71e8a5e1a44211b98e408209: regression test test_collapsed_tree_remnants_still_mature_without_new_growth in tests/test_autonomous_provisioning_c003.py.
- db6c6cb39185aac05bdac568bc920b88b4f25725: reconcile both exact-source SHA-256 manifest entries; unchanged count 516.
Source SHA256: 8d1ae4f598dd2d7af944486d6a5221e49451e6dc4e85ed474579bed816ae3ef3.
Test SHA256: b6a7ea1660a8d8cb836668a653a5bfb3a8e48b6c7cf52072d6d276a74f31869c.
Manifest blob: a04659124604662e27d71e11c27565a8a5d5aab6.
Rollback: reviewed revert of the three commits, not force push.

## III RUN_MANIFEST
Source: Development at db6c6cb39185aac05bdac568bc920b88b4f25725. New test: committed, NOT EXECUTED. CI workflow lookup and combined commit statuses returned no results. Local checkout: github.com DNS resolution failed. Seeds: NONE newly executed (test fixture uses bootstrap seed 821). Arms: none. Horizons: none. Conservation audit: test asserts Book.audit(), but execution unverified. Checkpoint replay: same-age policy tick asserted in test, execution unverified. No raw simulation output exists.
Reproduce: python tools/u026_g2_exact_source_audit.py; cd Founders_CIV_CoreCompletion151/source/world023024 && PYTHONPATH=. python -m pytest -q tests/test_autonomous_provisioning_c003.py; PYTHONPATH=. python -m pytest -q tests; negative source mutation/unlisted-test controls; G1 matched checks.

## IV Analysis / decision
REVISE. The change enables maturation/decay processing for collapsed Tree remnants when the provisioning policy is ticked; it does not guarantee the global scheduler ticks archived Trees. It neither establishes ecological stability nor a complete two-World system. Verify scheduler behavior and collapse/decay conservation before promotion.

## V Branch reconciliation and queue
Only Development changed; Core, Integration, Outer and main untouched. Draft Development→Core PR #3 remains unmerged. G0/G1 historical acceptance; G2 C024 current-source regression pending; G3 unpromoted; G4 unverified; WB-PKG incomplete; G5+ blocked.
Next: run C024 CI, inspect scheduler dispatch to archived Trees, then implement two independently advancing Worlds with one Book, World-qualified Tree accounts and checkpoint replay. Preserve P1-09 native read-only actor epoch reconciliation, P2-11 WB-PKG-gated gameplay, P2-12 CIV-OS research. No native gameplay, Windows DLL or live WorldBox claims.
