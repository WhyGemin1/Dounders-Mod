# U026 WorldBox Phase 4: M01 native animal identity — live game acceptance

**Cycle:** Phase4-M01-001. **Branch:** existing Dounders-Mod `Development`. **Goal:** observe the same real native WorldBox animals before and after saving/reloading a disposable WorldBox world. This is a read-only M01 bridge extension, **not** another engine or a G2/G3/G4 promotion.

## Verified before installing

- M05.4 live capture: 14,736 native callback events, 0 gaps/loss, 4,856 observed actor IDs, 7 hook registrations, functioning Unity heartbeat. Event and nutrition semantics remain provisional.
- New M01 command: `query_actor_identities` under the user's separate `WhyGemin1/worldbox-mcp` fork. Native signature `ActorData.id` and parent fields need live confirmation.
- Exact native build source is pinned to fork commit `e98d4f7062eb6fe21b590108de6c4545aa158f19`. CI compiles the patched native C# bridge and executes .NET tests. This is **not** a substitute for running it inside WorldBox.
- WorldBox 0.51.2 `Assembly-CSharp.dll` SHA-256: `51d275f0168be2f6ca26341ab292406714e694e0270eafcb25b999d5df6dd69f`. Never replace the installed game DLL to satisfy the guard.

## Prerequisites and safe Windows deployment

1. Back up a disposable WorldBox save and `BepInEx/plugins`; close WorldBox. Never upload Steam keys, auth tokens, proprietary game DLLs, or private saves.
2. In a **new PowerShell session** you can temporarily allow local scripts with `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force` if your account permits. Do not weaken machine-wide policy.
3. Update the existing local Founders–CIV checkout:
   ```powershell
   git -C 'C:\Dev\Dounders-Mod' pull --ff-only origin Development
   ```
4. Run the **build/test-only** check first:
   ```powershell
   & 'C:\Dev\Dounders-Mod\Founders_CIV_WorldBox_M01\Phase4-PrepareIdentityBridge.ps1' -GameDir 'C:\Program Files (x86)\Steam\steamapps\common\WorldBox'
   ```
   Require `M01 BUILD PASS`. This script checks exact installed native assembly, BepInEx 5, pinned fork revision, patches the C# command idempotently, builds with warnings as errors and executes .NET tests. The only direct fork edits are in `C:\Dev\worldbox-mcp`; it never modifies Core151 or M05.
5. Close WorldBox, then explicitly install if the build passed:
   ```powershell
   & 'C:\Dev\Dounders-Mod\Founders_CIV_WorldBox_M01\Phase4-PrepareIdentityBridge.ps1' -GameDir 'C:\Program Files (x86)\Steam\steamapps\common\WorldBox' -Install
   ```
   Require `M01 INSTALL PASS`. A previous `WorldBoxBridge.dll` is backed up, and installed SHA-256 must equal the build SHA-256. **Do not** use the upstream release installer for this run; it would replace the locally patched bridge and may alter existing BepInEx setup.

## Live scenario — first paired snapshots

1. Start WorldBox and load the disposable test world. Make sure the existing M05 observer still starts. Select at least 20 native animals, ideally small enough for the **complete** 5,000-actor M01 limit. Pause a fully loaded world.
2. Use the M01 live authentication script; it loads the local token into the process environment without printing it. **Never paste that token in ChatGPT**.
   ```powershell
   & 'C:\Dev\Dounders-Mod\Founders_CIV_WorldBox_M01\Phase4-RunLiveIdentity.ps1' -Stage probe
   & 'C:\Dev\Dounders-Mod\Founders_CIV_WorldBox_M01\Phase4-RunLiveIdentity.ps1' -Stage before
   ```
   First require working `/health` and `/capabilities`. The second command creates `%USERPROFILE%\Documents\FoundersCIV-Phase4\M01_before.json` after validating a full paused native ID query. If an ID is missing, do **not** use actor names or coordinates as substitutes.
3. Save this world using WorldBox's normal in-game save control. Close the game normally, reload the **same save slot**, pause, and capture:
   ```powershell
   & 'C:\Dev\Dounders-Mod\Founders_CIV_WorldBox_M01\Phase4-RunLiveIdentity.ps1' -Stage after
   & 'C:\Dev\Dounders-Mod\Founders_CIV_WorldBox_M01\Phase4-RunLiveIdentity.ps1' -Stage compare
   ```
4. The comparison creates `M01_reload_comparison.json`. Inspect the `identity_and_lineage_pass` result, `missing_or_changed`, and `new_actor_ids`. A zero-diff comparison is **provisional** until native actor IDs are correlated with the actual saved-world identity. Matching `world_seed` and an operator-created `world_key` do not prove the same save.
5. Repeat on **20 genuine save/reload trials** to investigate persistence. Use copies of validated snapshots and a named run manifest for each trial. New world generations or new animal spawns invalidate a matched static-control comparison.

## Strict gates

- **P0 — native build:** correct DLL signature; C# build, .NET tests, installed SHA, no compromise to M05.
- **P0 — real read:** command appears in bridge capabilities and returns complete paused actor IDs, correct species/lineage structure and meaningful values. Missing or ambiguous IDs block.
- **P0 — persistence:** at least 20 real save/reload pairs with stable actors; no unexplained ID collision, parent reassignment, false factory births or incomplete snapshots. Source-identified save identity and manually logged save slot must be present.
- **P1 — biology:** correlate logged birth and kill callbacks with actual offspring/parent IDs and verified death transitions. Raw callback counts are **not** biological facts; nutrition is **not** calibrated BIO.
- Never write native nutrition or inferred birth/kill outcomes to Core151's authoritative Book. No Tree feeding, reproduction edits, or G4 ecology promotion without separately reviewed mechanics.

## What to report back

Upload or share redacted `M01_reload_comparison.json`, a small subset of `M01_before.json` and `M01_after.json` (remove private names if any), and the build failure text if encountered. Do not share `WorldBoxBridge.cfg` or `WORLDBOX_MCP_TOKEN`. Record `M01 GATE: REVISE / LIVE UNVERIFIED` until the 20 genuine pairs pass.

**Limit:** This cycle prepares and offline-builds a real native identity bridge. It cannot directly launch or control the user's Windows WorldBox process from GitHub CI. The native game trial requires the user's PC.
