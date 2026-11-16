# Founders-CIV Phase 2: verify installed game, compile M05.3, optionally install.
# Requires your existing licensed WorldBox + BepInEx 5 installation on Windows.
# This script never copies or redistributes native WorldBox DLLs.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$GameDir,
    [switch]$Install
)
$ErrorActionPreference = 'Stop'
$expected = '51d275f0168be2f6ca26341ab292406714e694e0270eafcb25b999d5df6dd69f'
$game = (Resolve-Path -LiteralPath $GameDir -ErrorAction Stop).Path
$project = $PSScriptRoot
$managed = Join-Path $game 'WorldBox_Data\Managed'
$asm = Join-Path $managed 'Assembly-CSharp.dll'
$buildScript = Join-Path $project 'build_bridge.ps1'

if (Get-Process -Name 'WorldBox' -ErrorAction SilentlyContinue) {
    throw 'Close WorldBox before building/installing M05.3. No files changed.'
}
if (-not (Test-Path -LiteralPath $asm -PathType Leaf)) {
    throw "No installed WorldBox assembly at $asm. No files changed."
}
$actual = (Get-FileHash -LiteralPath $asm -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -ne $expected) {
    throw "MISMATCH_FAIL_CLOSED: installed WorldBox SHA256 is $actual, not $expected. Do NOT replace the game's DLL."
}
if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
    throw 'dotnet SDK not installed or not available in PowerShell PATH. No files changed.'
}
$deps = @(
    (Join-Path $game 'BepInEx\core\BepInEx.dll'),
    (Join-Path $game 'BepInEx\core\0Harmony.dll'),
    (Join-Path $managed 'UnityEngine.dll'),
    (Join-Path $managed 'UnityEngine.CoreModule.dll'),
    (Join-Path $managed 'UnityEngine.IMGUIModule.dll'),
    (Join-Path $managed 'UnityEngine.JSONSerializeModule.dll')
)
foreach ($dep in $deps) {
    if (-not (Test-Path -LiteralPath $dep -PathType Leaf)) {
        throw "Missing local BepInEx/Unity dependency: $dep. No files changed."
    }
}
if (-not (Test-Path -LiteralPath $buildScript -PathType Leaf)) {
    throw "Missing M05 build script: $buildScript"
}
$csproj = Join-Path $project 'bridge\FoundersCIV_M05_Observer.csproj'
$source = Join-Path $project 'bridge\FoundersCIV_M05_Observer.cs'
if (-not (Test-Path -LiteralPath $csproj) -or -not (Test-Path -LiteralPath $source)) {
    throw 'Missing M05.3 C# project/source. Use the updated Development checkout.'
}
if (-not ((Get-Content -LiteralPath $csproj -Raw).Contains('UnityEngine.JSONSerializeModule'))) {
    throw 'The C# project is older than M05.3. Update the Development checkout.'
}
if (-not ((Get-Content -LiteralPath $source -Raw).Contains('new HarmonyMethod(finalizer), null);'))) {
    throw 'The Harmony source is older than M05.3. Update the Development checkout.'
}
if ($Install) {
    $worldKeyPath = Join-Path $game 'BepInEx\FoundersCIV_M05\world_key.txt'
    if (-not (Test-Path -LiteralPath $worldKeyPath -PathType Leaf)) {
        throw "Missing save-specific world key $worldKeyPath. Run build-only first and configure a disposable test save."
    }
    $worldKey = (Get-Content -LiteralPath $worldKeyPath -Raw).Trim()
    if ([string]::IsNullOrWhiteSpace($worldKey) -or $worldKey -eq 'UNBOUND') {
        throw 'World key must identify a disposable save before installation.'
    }
}
Write-Host "Phase 2 preflight PASS; installed Assembly-CSharp SHA256 = $actual" -ForegroundColor Green
Write-Host "dotnet SDK: $(dotnet --version)"
Write-Host 'M05.3 dependencies: 6/6 present; build uses local copies only.'
if ($Install) {
    & $buildScript -GameDir $game -Install
} else {
    & $buildScript -GameDir $game
}
$dll = Join-Path $project 'build\Release\FoundersCIV_M05_Observer.dll'
if (-not (Test-Path -LiteralPath $dll -PathType Leaf)) {
    throw 'M05.3 build did not produce its expected DLL.'
}
$buildHash = (Get-FileHash -LiteralPath $dll -Algorithm SHA256).Hash.ToLowerInvariant()
if ($Install) {
    $installed = Join-Path $game 'BepInEx\plugins\FoundersCIV_M05_Observer.dll'
    if (-not (Test-Path -LiteralPath $installed -PathType Leaf)) {
        throw 'Installation did not create the expected plugin DLL.'
    }
    $installedHash = (Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($buildHash -ne $installedHash) {
        throw 'Installed DLL differs from the freshly built DLL. Do not launch WorldBox.'
    }
    Write-Host "PHASE 2 INSTALL PASS: installed SHA256 $installedHash" -ForegroundColor Green
} else {
    Write-Host "PHASE 2 BUILD PASS: DLL SHA256 $buildHash; nothing installed." -ForegroundColor Green
}
