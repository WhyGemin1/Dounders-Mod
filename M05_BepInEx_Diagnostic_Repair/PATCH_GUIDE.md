# M05 v0.5.2 — WorldBox bridge repair: game-local dependency staging

## What the screenshot proves

PowerShell ends with **22 errors and 1 warning**. Visible lines show `CS0012`: `MonoBehaviour` in `UnityEngine, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null` is not referenced. The exception in `build_bridge.ps1` means **the installer did not run**. No game modification is evidenced by this failed build.

This is **a compile-time dependency resolution error**, not an animal simulation or Python/SQLite error. The v0.5.1 patch added `UnityEngine.dll` via an MSBuild `$(GameDir)` property, but that approach still depends on the edited project actually being used and the MSBuild property resolving correctly. The repeated screenshot does not prove that v0.5.1 was successfully applied.

## What this release changes

1. `build_bridge.ps1` checks the exact SHA256 of installed `Assembly-CSharp.dll` (no version spoofing). 
2. It verifies the five required BepInEx/Harmony/Unity engine references exist in **your** game installation.
3. It copies those DLLs to the local `build/refs` folder and verifies that copied hashes match the source files. DLLs are not bundled or distributed in this ZIP.
4. The `.csproj` uses only **relative paths** to the staged DLLs, including the missing `UnityEngine.dll`; it no longer depends on an MSBuild `GameDir` property or PowerShell path quoting.
5. The build clears old generated `Release`, `obj`, and `bin` outputs first; it doesn't touch `data`, `local_world.json`, or user saves.
6. It checks compilation success and the resulting DLL before installing; when updating, it backs up the previous M05 plugin outside `BepInEx/plugins`.
7. A small event-stream durability fix writes each pending JSON line **before** removing it from the memory queue.
8. Four structural regression tests verify these build provisions. They do **not** replace compiling inside your game environment.

## Apply the repair to your EXISTING M05 installation

1. Close WorldBox. Back up your save, and keep `C:\Dev\FoundersCIV_WorldBox_M05_Integration\data\house.sqlite` and `local_world.json` unchanged.
2. Extract `FoundersCIV_WorldBox_M05_v0.5.2_REPAIR.zip` to `C:\Dev\M05_052_Repair`. The root should contain `Repair-M05.ps1` and the `payload` folder.
3. PowerShell commands (paste **one block at a time**):

```powershell
$game = 'C:\Program Files (x86)\Steam\steamapps\common\WorldBox'
$project = 'C:\Dev\FoundersCIV_WorldBox_M05_Integration'

& 'C:\Dev\M05_052_Repair\Repair-M05.ps1' -ProjectRoot $project -GameDir $game -Build
```

4. Success must explicitly say **`M05.2 build PASSED:`**. If it still reports `CS0012`, copy the **first error and the dependency manifest** (located at `build\dependency_manifest.json`) for further investigation; don't install.
5. Once build passed, install the compiled DLL by running:

```powershell
& "$project\build_bridge.ps1" -GameDir "$game" -Install
```

6. Check the plugin file exists:

```powershell
Test-Path "$game\BepInEx\plugins\FoundersCIV_M05_Observer.dll"
```

7. Launch WorldBox on **a backed-up experimental save** only, check BepInEx logs for `M05 event observer started`, exactly seven active hooks, and review the native event audit after closing.

## Manual diagnostics, before installation

```powershell
Get-Content "$project\bridge\FoundersCIV_M05_Observer.csproj" | Select-String 'Reference Include="UnityEngine"|build/refs'
Get-ChildItem "$project\build\refs" | Select-Object Name,Length
Get-Content "$project\build\dependency_manifest.json"
```

The files in `build/refs` are local build inputs copied from the game, **not files you should move into BepInEx/plugins**. Do not ship them with the package.

## Rollback of the repair

`Repair-M05.ps1` creates a `M05_052_backup_YYYYMMDD_HHMMSS` folder in the existing project folder containing the previous C# project, bridge, and build script. To revert, close WorldBox and copy those backups over the new files. The M05 virtual energy database and game save are not edited by the repair.

## Evidence levels

- Verified here: project XML, repair package layout, Python regression tests, correct uploaded `Assembly-CSharp.dll` fingerprint.
- **Not verified here:** actual C# compiler success against your local Unity/BepInEx DLLs, runtime Harmony hook attachment, live native events, Core151 Book integration, or real World Tree/fruit spawning in WorldBox.
