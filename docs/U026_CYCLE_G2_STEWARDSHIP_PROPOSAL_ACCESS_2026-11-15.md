# U026 G2 cycle — eliminate impossible remote stewardship proposals

Date: 2026-11-15 (America/Chicago)
Assignment: G2 Founder physical-access consistency, real Core151 source on Development.
Decision: REVISE / NOT PROMOTED.

## I. Baseline and falsifier
Previous G2 implementation already rejected new remote tend_parent transfers, but propose_parent_stewardship still offered the action to a Founder whose observation was fresh and who had traveled from house/riverbank to ridge. This caused an impossible selected action and avoidable rejections. Hypothesis: gating only the proposal (not stored observation, prior Book receipt or private choices) prevents invalid offers while preserving valid local stewardship. Falsifier: remote actor still gets parent_steward, or returning actor cannot propose, or any Book resource is moved by proposal.

## II. Executable source changes
Commit 11e547178151028408ca4506d6945fb01a5def32: Founders_CIV_CoreCompletion151/source/world023024/founders_civ/core/founder_parent_stewardship.py. Insert local-access guard after the fresh-observation check and before the reserve forecast. Remote actors retain private reserve knowledge but no longer receive a physically impossible proposal.
Commit 4b6c10ec01529b995a2047419b6a0b38f5afc7d9: Founders_CIV_CoreCompletion151/source/world023024/tests/test_u026_g2_parent_stewardship.py. New regression checks that a Founder at riverbank has a stewardship proposal, loses the proposal after moving to ridge, retains unchanged Book balances/sequence and event counts, and regains the proposal after returning; Book.audit invoked.
No WorldBox native physiology or Core branch changes.

## III. Reproducible tests and RUN_MANIFEST
Source commit: 4b6c10ec01529b995a2047419b6a0b38f5afc7d9.
Source blobs after update: policy 8043662a084065d983cc0f0000a569ec368bf359; test f6693cc744388887827fcf2643409cbb392ee8c0.
Target root: Founders_CIV_CoreCompletion151/source/world023024.
Focused command: PYTHONPATH=. python -m pytest -q tests/test_u026_g2_parent_stewardship.py
Full command: PYTHONPATH=. python -m pytest -q tests
Status: NOT_RUN in this cycle. GitHub Actions workflow runs for the exact test commit: none at check time; commit combined statuses: none. Local container cannot reach github.com (DNS failure) and no complete repository checkout was mounted. No seed, arm, horizon, simulation result, conservation audit or replay result was generated for this change. Existing previous-cycle tests are not counted as this commit's tests.
The existing exact-source candidate fingerprint MUST be regenerated after the two changed files; until then source audit should fail closed, and promotion is blocked. Do not claim 515 hashes passed for this commit.

## IV. Ecological interpretation
This fixes an agent-policy/physical-action mismatch; it does not increase food production or prove ecological improvement. Alternative hypothesis for high rejected actions: stale knowledge, poor opportunity scores, or insufficient work fuel rather than distance. Once tests run, compare matched control versus new proposal guard with unchanged initial seed and stocks. Measure proposal counts, rejected parent actions, actual stewardship transfers, parent survival and resource conservation. No G2 promotion.

## V. Branch roles and handoff
At audit, Development was 151 commits ahead of Core, Integration and Outer (all base c935c9a7066d6fe8d122a46edd2d8ce223343be2), and 151 ahead / 1 behind main (main base 26a02ba50a53770b14eae0368315ea01036d0b3c). Following two new source/test commits Development is at least 153 ahead of Core; no merge, force push or PR acceptance was attempted.
Development owns this candidate; Core stays reviewed-only; Integration awaits full source, regression and cross-system acceptance; Outer owns WorldBox observer/build/rollback package; main stays stable. PR #3 remains review-only. Native WorldBox and WB-PKG unverified.
Next task: refresh 515-path candidate SHA256 fingerprint, execute focused/full tests and exact-source CI from GitHub checkout, run matched 30/180-day controls, then review physical opportunity-access effects. P1-09 identity/epochs, P1-10 two independent Worlds and P2-11 native Tree/fruit gameplay remain in queue behind WB-PKG; G4 juvenile prey, density, predator recruitment and migration remain unpromoted. No source ZIP or raw test output is claimed to exist for this cycle.

Gate status: G0/G1 historical Development accepted revisions; G2 REVISE, unpromoted; G3/G4 unpromoted; WB-PKG/G5+ unverified.
GitHub write permission: CONFIRMED by returned source/test commit SHA and blob SHA.
