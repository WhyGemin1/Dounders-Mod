# Founders–CIV × WorldBox — M05.3 focused C# build repair

Repairs the three compiler errors shown in November 13 screenshots:
- CS0619 at the Harmony Patch call, by using the supported six-argument overload;
- CS0103 at both JsonUtility call sites, by staging and referencing UnityEngine.JSONSerializeModule.dll.

Does NOT replace M05 Python / SQLite model, local_world.json, WorldBox files, or saves.

## PowerShell — run each block separately

1. Close WorldBox. Download `FoundersCIV_WorldBox_M05_v0.5.3_REPAIR.zip` to Downloads.

```powershell
$zip = Join-Path $env:USERPROFILE 'Downloads\FoundersCIV_WorldBox_M05_v0.5.3_REPAIR.zip'
Test-Path -LiteralPath $zip
```

Only proceed when it prints `True`. Otherwise locate the ZIP (download may have a `(1)` suffix).

2. Extract the ZIP, then check that the script exists:

```powershell
$fix = 'C:\Dev\M05_053_Repair'
New-Item -ItemType Directory -Path $fix -Force | Out-Null
Expand-Archive -LiteralPath $zip -DestinationPath $fix -Force
Test-Path -LiteralPath "$fix\Repair-M05.ps1"
```

3. Check game dependency before touching project:

```powershell
$game = 'C:\Program Files (x86)\Steam\steamapps\common\WorldBox'
$project = 'C:\Dev\FoundersCIV_WorldBox_M05_Integration'
Test-Path -LiteralPath "$game\WorldBox_Data\Managed\UnityEngine.JSONSerializeModule.dll"
```

Expected `True`. If `False`, stop and share output and `Get-ChildItem "$game\WorldBox_Data\Managed\UnityEngine*" | Select-Object Name` (no need to reinstall anything).

4. Repair and compile, without installing:

```powershell
& "$fix\Repair-M05.ps1" -ProjectRoot $project -GameDir $game -Build
```

5. **Only if** you see `M05.3 BUILD SUCCESS`, install:

```powershell
& "$project\build_bridge.ps1" -GameDir $game -Install
Test-Path -LiteralPath "$game\BepInEx\plugins\FoundersCIV_M05_Observer.dll"
```

There are still no verified in-game observations until WorldBox is launched and native sessions audited. Do not interpret successful compilation as verified gameplay integration.

## If an error occurs

In PowerShell, show the **first error** (not just the final red line). To capture build output:

```powershell
& "$project\build_bridge.ps1" -GameDir $game *>&1 | Tee-Object -FilePath "$project\build\m05_053_compile_log.txt"
```

Check extracted path before running any script. If the prompt starts with `>>`, press Ctrl+C and run each line separately.

## Rollback

The script creates `$project\M05_053_backup_YYYYMMDD_HHMMSS` with the original source/project/build script. Restore those three files if needed. No save, database, or game binary was modified by the repair.
