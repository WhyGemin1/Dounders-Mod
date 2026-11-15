# M05.3: fail-closed, reproducible game-local assembly build.
# Uses local DLLs copied from YOUR WorldBox install, never redistributes them.
param(
    [Parameter(Mandatory=$true)][string]$GameDir,
    [switch]$Install
)
$ErrorActionPreference = 'Stop'

$game = (Resolve-Path -LiteralPath $GameDir -ErrorAction Stop).Path
$managed = Join-Path $game 'WorldBox_Data\Managed'
$core = Join-Path $game 'BepInEx\core'
$asm = Join-Path $managed 'Assembly-CSharp.dll'
$expected = '51d275f0168be2f6ca26341ab292406714e694e0270eafcb25b999d5df6dd69f'
if (-not (Test-Path -LiteralPath $asm -PathType Leaf)) {
    throw "WorldBox assembly missing: $asm. No files changed."
}
$actual = (Get-FileHash -LiteralPath $asm -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -ne $expected) {
    throw "WorldBox binary MISMATCH_FAIL_CLOSED: expected $expected; actual $actual. DO NOT replace your game DLL. No installation."
}
if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
    throw 'dotnet SDK not found. Install the SDK and restart PowerShell. No installation.'
}

$project = Join-Path $PSScriptRoot 'bridge\FoundersCIV_M05_Observer.csproj'
$source = Join-Path $PSScriptRoot 'bridge\FoundersCIV_M05_Observer.cs'
if (-not (Test-Path -LiteralPath $project) -or -not (Test-Path -LiteralPath $source)) {
    throw "Bridge source/project missing under $PSScriptRoot. No installation."
}
$xmlText = [System.IO.File]::ReadAllText($project)
[xml]$xml = $xmlText
foreach ($name in @('UnityEngine','UnityEngine.CoreModule','UnityEngine.IMGUIModule','UnityEngine.JSONSerializeModule','BepInEx','0Harmony')) {
    $expectedRef = '<Reference Include="' + $name + '">'
    if (-not $xmlText.Contains($expectedRef)) {
        throw "Incorrect M05.3 project: missing reference $name. Apply M05.3 repair patch first. No installation."
    }
}
if (-not ([System.IO.File]::ReadAllText($source).Contains('new HarmonyMethod(finalizer), null);'))) {
    throw 'M05.3 source not installed: obsolete Harmony overload still present. Stop before build.'
}
$deps = [ordered]@{
    'BepInEx.dll' = (Join-Path $core 'BepInEx.dll')
    '0Harmony.dll' = (Join-Path $core '0Harmony.dll')
    'UnityEngine.dll' = (Join-Path $managed 'UnityEngine.dll')
    'UnityEngine.CoreModule.dll' = (Join-Path $managed 'UnityEngine.CoreModule.dll')
    'UnityEngine.IMGUIModule.dll' = (Join-Path $managed 'UnityEngine.IMGUIModule.dll')
    'UnityEngine.JSONSerializeModule.dll' = (Join-Path $managed 'UnityEngine.JSONSerializeModule.dll')
}

$missing = @()
foreach ($depName in $deps.Keys) {
    if (-not (Test-Path -LiteralPath $deps[$depName] -PathType Leaf)) {
        $missing += "$depName => $($deps[$depName])"
    }
}
if ($missing.Count -ne 0) {
    throw "Missing game-local build dependencies (no installation):`n$($missing -join "`n")"
}

$refDir = Join-Path $PSScriptRoot 'build\refs'
$out = Join-Path $PSScriptRoot 'build\Release'
$obj = Join-Path $PSScriptRoot 'bridge\obj'
$bin = Join-Path $PSScriptRoot 'bridge\bin'
New-Item -ItemType Directory -Path $refDir -Force | Out-Null
$manifest = @()
foreach ($depName in $deps.Keys) {
    $from = $deps[$depName]
    $to = Join-Path $refDir $depName
    Copy-Item -LiteralPath $from -Destination $to -Force
    $a = (Get-FileHash -LiteralPath $from -Algorithm SHA256).Hash.ToLowerInvariant()
    $b = (Get-FileHash -LiteralPath $to -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($a -ne $b) { throw "Dependency staging hash mismatch: $depName. No installation." }
    $manifest += [pscustomobject]@{assembly=$depName; sha256=$a; staged=$to}
}
$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'build\dependency_manifest.json') -Encoding UTF8

# Avoid accidentally reusing artifacts that were compiled with the old broken project.
foreach ($generated in @($out, $obj, $bin)) {
    if (Test-Path -LiteralPath $generated) { Remove-Item -LiteralPath $generated -Recurse -Force }
}
Write-Host 'M05.3: staged local Unity/BepInEx/Harmony references:' -ForegroundColor Cyan
foreach ($name in $deps.Keys) { Write-Host "  $name" }
Write-Host "Building project: $project" -ForegroundColor Cyan
Write-Host 'Native game modifications: NONE'

# No -p:GameDir argument: paths with spaces are no longer an MSBuild input.
& dotnet build $project --configuration Release --output $out --no-incremental --verbosity minimal
if ($LASTEXITCODE -ne 0) {
    throw 'M05.3 build FAILED. No installation. Read compiler errors above; dependency hashes in build\dependency_manifest.json.'
}
$dll = Join-Path $out 'FoundersCIV_M05_Observer.dll'
if (-not (Test-Path -LiteralPath $dll -PathType Leaf)) {
    throw 'Compiler returned success but observer DLL is absent. No installation.'
}
Write-Host "M05.3 build PASSED: $dll" -ForegroundColor Green
if (-not $Install) {
    Write-Host 'Build-only mode. Run again with -Install only after confirming the build passed.'
    return
}

$plugins = Join-Path $game 'BepInEx\plugins'
if (-not (Test-Path -LiteralPath $plugins)) {
    throw 'No BepInEx/plugins folder. Confirm correct game installation. No installation.'
}
$older = @(Get-ChildItem -LiteralPath $plugins -Recurse -Filter '*.dll' -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match 'M03.*Event|Event.*M03' })
if ($older.Count -gt 0) {
    throw "Old M03 observer(s) found: $($older.FullName -join ', '). Move them OUT of plugins first. No installation."
}
$dest = Join-Path $plugins 'FoundersCIV_M05_Observer.dll'
if (Test-Path -LiteralPath $dest) {
    $backupDir = Join-Path $PSScriptRoot 'build\plugin_backups'
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    Copy-Item -LiteralPath $dest -Destination (Join-Path $backupDir "FoundersCIV_M05_Observer.$stamp.dll.bak") -Force
}
Copy-Item -LiteralPath $dll -Destination $dest -Force
$srcHash = (Get-FileHash -LiteralPath $dll -Algorithm SHA256).Hash
$dstHash = (Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash
if ($srcHash -ne $dstHash) { throw 'Installed DLL hash mismatch. Remove it; do not launch the game.' }
Write-Host "INSTALLED M05.3 observer: $dest" -ForegroundColor Green
Write-Host 'Keep game closed until your save-specific BepInEx\FoundersCIV_M05\world_key.txt is set.'
