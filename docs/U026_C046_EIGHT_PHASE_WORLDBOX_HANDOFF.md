# U026 C045 Five-Phase + C046 Eight-Phase WorldBox Offline Handoff

Date: 2026-11-17. Repository: WhyGemin1/Dounders-Mod. Branch: Development.
Decision: REVISE / keep all mechanics on Development; **no live WorldBox certification**.

## C045 five-phase cycle

1. Baseline: C044 Windows workflow 44178823336 failed in C# smoke build with CS0649 for five Unity-serialized projection fields. Its 49 M05 Python source/unit tests and 15 synthetic capture tests passed.
2. Implementation: commit `627090bb0117af9855eaf28fda57a1c3e25edfa6` explicitly initializes those fields to their existing zero/false defaults in the actual M05 observer. No native gameplay mutation.
3. Testing: workflow 44186586578 **success**: M05 49 Python tests, 15/15 Windows capture fixtures, actual observer source compiled with test-only API stubs and queue smoke passed. M01 build workflow 44186586668 **success**.
4. Decision: REVISE; only the warning-clean offline compiler gate is accepted, not real game build or ecology.
5. Reconciliation: leave Core/Integration/Outer/main untouched; no PR merge.

## C046 eight-phase follow-up

1. Audit: inspect real M05 observation code, its fail-closed PowerShell event gate, Windows fixture suite, C# smoke and branch responsibilities. Native game is authoritative.
2. Causal hazard: a disabled observer could still emit native callback events/heartbeats, and a session containing a mid-capture disable could be accepted even if hooks were no longer monitoring the game.
3. Code: `be3ee2fbaad95d1d022b05afe78ab0d1ff214370` stops native Send() callbacks and new Update() heartbeats/projections after disable, flushing already pending records.
4. Acceptance semantics: `54d3ec1b02dba606fa10165cf39dc9213b4630e6` makes a session containing observer_disabled fail closed rather than certify native behavior.
5. Windows negative control: `ed3144364a513c348bd5e9c1a85b847cb85254d1` expands capture fixtures to 16 cases, with new deliberately disabled session rejection.
6. Source contract: `1d369df9cd3d8627ca964be42dd89280646a9a99` updates Python assertions for the changed fail-closed semantics.
7. Executable C# integration: `c3c8de39bc73fd29d33b2d863c43b4c73cdf959d` tests disable.flag, Harmony unpatch, single disable event, no subsequent heartbeat, no further native callback and no automatic re-enable without restart. Windows CI 44187000358 **success**: 49/49 Python tests; 16/16 fixtures; executable 50,000 queue/loss smoke and disable smoke both PASS. M01 offline bridge build 44187000385 **success**.
8. Decision and reconciliation: REVISE. Existing Core/Main remain unchanged. Do not label a test-only API-stub compile as a real WorldBox DLL build; do not perform a live gameplay test without WB-PKG and copied-save/backup/restore verification.

## Acceptance evidence

- C045 Windows: https://github.com/WhyGemin1/Dounders-Mod/actions/runs/44186586578
- C046 Windows: https://github.com/WhyGemin1/Dounders-Mod/actions/runs/44187000358
- C046 M01 offline bridge: https://github.com/WhyGemin1/Dounders-Mod/actions/runs/44187000385
- C046 full Core151 source, conservation, provenance, G1 matched: https://github.com/WhyGemin1/Dounders-Mod/actions/runs/44187000445 **success** (327 Python regression tests; 17 G1 exact replay, 12 G2 stewardship, fail-closed provenance, G1 matched 10 seeds x 2 arms = 20 runs at 30/180 days)
- Prior verified C042 Core151: https://github.com/WhyGemin1/Dounders-Mod/actions/runs/44169067653
- PR #3 Development -> Core remains draft and unmerged: https://github.com/WhyGemin1/Dounders-Mod/pull/3

## Run manifest

| Evidence | Source | Result | Scope |
| --- | --- | --- | --- |
| C044 initial CI | prior SHA 1b99671a8c697b5690d62dd26c74d6c0ba8fc6b5 | FAIL CS0649 | C# test-only source compile |
| C045 Windows | 627090bb0117af9855eaf28fda57a1c3e25edfa6 | PASS | 49 M05 unit + 15 synthetic Windows captures + C# queue smoke |
| C046 Windows | c3c8de39bc73fd29d33b2d863c43b4c73cdf959d | PASS | 49 M05 tests + 16 synthetic captures + C# queue/disable smoke |
| C046 M01 | c3c8de39bc73fd29d33b2d863c43b4c73cdf959d | PASS | pinned source bridge compilation/testing, offline |
| C046 Core151 | c3c8de39bc73fd29d33b2d863c43b4c73cdf959d | PASS workflow 44187000445 | 327 full tests; 17 focused G1; 12 focused G2; 20 matched runs; source audit |
| Seeds/horizons added | N/A | 0 | No new C046 ecological or animal behavior run |
| Native gameplay | N/A | NOT RUN | No real Windows/BepInEx game observation |

## Rollback

Safe code rollback is by reverse application of C046 commits, limited to their reviewed files, in a new Development commit only after reviewing current source. Never force push. On a user's Windows game machine, **do not touch original saves**. If an observer is installed, create `BepInEx/FoundersCIV_M05/disable.flag` while the game is running for fail-closed observation shutdown, then exit the game and remove the observer DLL through the user's approved uninstall/rollback workflow. A disabling observer session is rejected from scientific evidence.

## Gate and assignment queue

- G0/G1: historical tests pass, formal Core promotion still subject to complete-source PR and acceptance.
- G2/G3: candidate mechanics; not promoted to Core. C046 does not change ecological physiology.
- G4: multi-generation ecological stability NOT verified.
- M01/M05: offline read-only safety improved, native game compatibility unverified.
- WB-PKG: BLOCKED by lack of actual user's game-local Windows assembly/DLL hashes, copied-save backup/restore demonstration, installed plugin load, hook-hit/event semantic diagnostics, complete installer/uninstaller and reviewer sign-off.
- G5+: blocked.
- Next P0: Windows game-local build-only against the *installed* WorldBox Assembly-CSharp.dll SHA and local six Unity/BepInEx/Harmony dependencies, backed up copied save, then verify rollback and hook semantics before any game run. Reject mismatched assembly; never ship proprietary game DLLs.
- Next P1: independently advancing two Worlds under one Book/scheduler/checkpoint; separate from native WorldBox worlds.

No ecological or native WorldBox improvements claimed from offline test passes alone.
