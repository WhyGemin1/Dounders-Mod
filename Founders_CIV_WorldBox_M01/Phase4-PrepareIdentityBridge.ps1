# Phase 4: compile M01 stable-ID read-only command against pinned WorldBox-MCP fork.
# Default = build/test only; -Install explicitly installs one DLL into the owned game.
# No native WorldBox binaries, save data, or auth tokens are copied to this repo.
[CmdletBinding()]
param(
    [string]$GameDir = 'C:\Program Files (x86)\Steam\steamapps\common\WorldBox',
    [string]$BridgeCheckout = 'C:\Dev\worldbox-mcp',
    [switch]$Install
)
$ErrorActionPreference = 'Stop'
$expectedGame = '51d275f0168be2f6ca26341ab292406714e694e0270eafcb25b999d5df6dd69f'
$pinnedSource = 'e98d4f7062eb6fe21b590108de6c4545aa158f19'
$game = (Resolve-Path -LiteralPath $GameDir -ErrorAction Stop).Path
$asm = Join-Path $game 'WorldBox_Data\Managed\Assembly-CSharp.dll'
$bepinex = Join-Path $game 'BepInEx\core\BepInEx.dll'
if (Get-Process -Name 'WorldBox' -ErrorAction SilentlyContinue) {
    throw 'Close WorldBox first. M01 cannot be installed while the game is running.'
}
if (-not (Test-Path -LiteralPath $asm -PathType Leaf)) { throw "Missing game assembly: $asm" }
$sha = (Get-FileHash -LiteralPath $asm -Algorithm SHA256).Hash.ToLowerInvariant()
if ($sha -ne $expectedGame) {
    throw "M01 assembly fingerprint mismatch: $sha. Do NOT replace any native game DLL."
}
if (-not (Test-Path -LiteralPath $bepinex -PathType Leaf)) {
    throw 'BepInEx 5 dependency missing. Preserve your existing M05 installation and stop.'
}
foreach ($name in 'git','py','dotnet') {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        throw "Missing tool $name; cannot build M01"
    }
}
if (-not (Test-Path -LiteralPath $BridgeCheckout)) {
    $parent=Split-Path -Parent $BridgeCheckout
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    & git clone 'https://github.com/WhyGemin1/worldbox-mcp.git' $BridgeCheckout
    if ($LASTEXITCODE -ne 0) { throw 'Could not clone your WorldBox bridge fork' }
}
if (-not (Test-Path (Join-Path $BridgeCheckout '.git'))) {
    throw 'BridgeCheckout is not a Git repository; refusing to modify unknown files.'
}
$head=(& git -C $BridgeCheckout rev-parse HEAD).Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $head -ne $pinnedSource) {
    throw "WorldBox bridge source differs from reviewed revision: $head. Expected $pinnedSource. Stop for review."
}
$patch=Join-Path $PSScriptRoot 'apply_to_worldbox_bridge.py'
& py $patch $BridgeCheckout
if ($LASTEXITCODE -ne 0) { throw 'M01 source patch failed; no DLL installed' }
$solution=Join-Path $BridgeCheckout 'mod\WorldBoxBridge.sln'
& dotnet restore $solution --locked-mode
if ($LASTEXITCODE -ne 0) { throw 'M01 .NET restore failed; no DLL installed' }
& dotnet build $solution --configuration Release --no-restore -warnaserror
if ($LASTEXITCODE -ne 0) { throw 'M01 C# compilation failed; no DLL installed' }
& dotnet test $solution --configuration Release --no-build --no-restore
if ($LASTEXITCODE -ne 0) { throw 'M01 bridge tests failed; no DLL installed' }
$out=Join-Path $BridgeCheckout 'mod\src\WorldBoxBridge\bin\Release\WorldBoxBridge.dll'
if (-not (Test-Path -LiteralPath $out -PathType Leaf)) {
    throw "Expected compiled WorldBoxBridge.dll missing: $out"
}
$outsha=(Get-FileHash -LiteralPath $out -Algorithm SHA256).Hash.ToLowerInvariant()
if (-not $Install) {
    Write-Host "M01 BUILD PASS; DLL SHA256 $outsha; nothing installed." -ForegroundColor Green
    exit 0
}
$pluginDir=Join-Path $game 'BepInEx\plugins'
New-Item -ItemType Directory -Path $pluginDir -Force | Out-Null
$target=Join-Path $pluginDir 'WorldBoxBridge.dll'
$backup=$null
if (Test-Path -LiteralPath $target -PathType Leaf) {
    $dir=Join-Path $game 'BepInEx\FoundersCIV_M01\plugin_backups'
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    $backup=Join-Path $dir ("WorldBoxBridge-before-M01-" + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.dll')
    Copy-Item -LiteralPath $target -Destination $backup -ErrorAction Stop
}
try {
    Copy-Item -LiteralPath $out -Destination $target -Force -ErrorAction Stop
    $installed=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($installed -ne $outsha) { throw 'Installed DLL fingerprint differs from compiled DLL' }
} catch {
    if ($backup -and (Test-Path -LiteralPath $backup)) {
        Copy-Item -LiteralPath $backup -Destination $target -Force
    } elseif (Test-Path -LiteralPath $target) {
        Remove-Item -LiteralPath $target -Force
    }
    throw
}
Write-Host "M01 INSTALL PASS; installed DLL SHA256 $outsha" -ForegroundColor Green
Write-Host "Previous WorldBoxBridge backup: $backup"
Write-Host 'M05 observer remains a separate BepInEx plugin and was not modified.'
Write-Host 'Next: open a disposable WorldBox save, pause, then run the live snapshot workflow.'
