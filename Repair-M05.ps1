# Founders-CIV M05.3 scoped C# build repair; never modifies the game save or game managed binaries.
[CmdletBinding()]
param(
    [string]$ProjectRoot = 'C:\Dev\FoundersCIV_WorldBox_M05_Integration',
    [string]$GameDir = 'C:\Program Files (x86)\Steam\steamapps\common\WorldBox',
    [switch]$Build
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $ProjectRoot -ErrorAction Stop).Path
$game = (Resolve-Path -LiteralPath $GameDir -ErrorAction Stop).Path
$payload = Join-Path $PSScriptRoot 'payload'
if (-not (Test-Path -LiteralPath (Join-Path $root 'm05.py') -PathType Leaf)) {
    throw "M05 project not found at $root. No changes made."
}
$managed = Join-Path $game 'WorldBox_Data\Managed'
$asm = Join-Path $managed 'Assembly-CSharp.dll'
$expected = '51d275f0168be2f6ca26341ab292406714e694e0270eafcb25b999d5df6dd69f'
if (-not (Test-Path -LiteralPath $asm -PathType Leaf)) { throw "WorldBox game DLL not found: $asm. No changes." }
if ((Get-FileHash -LiteralPath $asm -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
    throw 'Game assembly SHA256 does not match M05 target. Stop: no patch or install.'
}
$required = @(
    (Join-Path $game 'BepInEx\core\BepInEx.dll'),
    (Join-Path $game 'BepInEx\core\0Harmony.dll'),
    (Join-Path $managed 'UnityEngine.dll'),
    (Join-Path $managed 'UnityEngine.CoreModule.dll'),
    (Join-Path $managed 'UnityEngine.IMGUIModule.dll'),
    (Join-Path $managed 'UnityEngine.JSONSerializeModule.dll')
)
foreach ($dll in $required) {
    if (-not (Test-Path -LiteralPath $dll -PathType Leaf)) { throw "Required local DLL missing: $dll. No files replaced." }
}
$targets = @(
    'bridge\FoundersCIV_M05_Observer.csproj',
    'bridge\FoundersCIV_M05_Observer.cs',
    'build_bridge.ps1'
)
foreach ($rel in $targets) {
    if (-not (Test-Path -LiteralPath (Join-Path $payload $rel) -PathType Leaf)) { throw "Repair ZIP incomplete: payload\$rel" }
    if (-not (Test-Path -LiteralPath (Join-Path $root $rel) -PathType Leaf)) { throw "Original project missing: $rel" }
}
if (Get-Process -Name 'WorldBox' -ErrorAction SilentlyContinue) {
    throw 'Close WorldBox first. The repair has not changed anything.'
}
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backup = Join-Path $root "M05_053_backup_$stamp"
New-Item -ItemType Directory -Path $backup -Force | Out-Null
foreach ($rel in $targets) {
    $source = Join-Path $root $rel
    $dest = Join-Path $backup $rel
    New-Item -ItemType Directory -Path (Split-Path -Parent $dest) -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $dest -Force
}
Write-Host "Backup made: $backup" -ForegroundColor Green
foreach ($rel in $targets) {
    $source = Join-Path $payload $rel
    $dest = Join-Path $root $rel
    Copy-Item -LiteralPath $source -Destination $dest -Force
    $expectedHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
    $actualHash = (Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash
    if ($expectedHash -ne $actualHash) { throw "Patch copy mismatch on $rel. Restore $backup" }
    Write-Host "Patched + verified: $rel"
}
Write-Host 'M05.3 C# source repair applied; no save, database, local_world.json, or game DLL changed.' -ForegroundColor Green
if ($Build) {
    if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) { throw 'dotnet SDK not found. Sources repaired, build NOT run.' }
    Write-Host 'Compiling observer locally. This does NOT install a plugin.' -ForegroundColor Cyan
    & (Join-Path $root 'build_bridge.ps1') -GameDir $game
    $dll=Join-Path $root 'build\Release\FoundersCIV_M05_Observer.dll'
    if (-not (Test-Path -LiteralPath $dll -PathType Leaf)) { throw 'Observer DLL absent after build. No installation.' }
    Write-Host "M05.3 BUILD SUCCESS: $dll" -ForegroundColor Green
}
