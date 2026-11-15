# Founders-CIV M05 BepInEx-aware build preflight / optional repair.
# No BepInEx config or secrets read; no game/save/database edits or automatic install.
[CmdletBinding()]
param(
    [string]$ProjectRoot = 'C:\Dev\FoundersCIV_WorldBox_M05_Integration',
    [string]$GameDir = 'C:\Program Files (x86)\Steam\steamapps\common\WorldBox',
    [switch]$Repair,
    [switch]$Build
)
$ErrorActionPreference = 'Stop'
function Check([string]$Label,[bool]$Pass,[string]$Explain) {
    if ($Pass) { Write-Host "PASS $Label - $Explain" -ForegroundColor Green }
    else { Write-Host "FAIL $Label - $Explain" -ForegroundColor Red }
    return $Pass
}
$game = (Resolve-Path -LiteralPath $GameDir -ErrorAction Stop).Path
$project = (Resolve-Path -LiteralPath $ProjectRoot -ErrorAction Stop).Path
$managed = Join-Path $game 'WorldBox_Data\Managed'
$core = Join-Path $game 'BepInEx\core'
$plugins = Join-Path $game 'BepInEx\plugins'
$expectedGame = '51d275f0168be2f6ca26341ab292406714e694e0270eafcb25b999d5df6dd69f'
$knownBep = 'c65b42034bc8ffb9f0b336e416dc3884e3f99fc5a5a89eb1f2ff7868412322cd'
$knownHarmony = '1a21cc03424fc82c3dd1346905d16494536b9595ae4162228d99fb7c285c1031'
$expectedFiles = [ordered]@{
    'WorldBox game assembly' = (Join-Path $managed 'Assembly-CSharp.dll')
    'BepInEx' = (Join-Path $core 'BepInEx.dll')
    'Harmony' = (Join-Path $core '0Harmony.dll')
    'UnityEngine facade' = (Join-Path $managed 'UnityEngine.dll')
    'UnityEngine CoreModule' = (Join-Path $managed 'UnityEngine.CoreModule.dll')
    'UnityEngine IMGUIModule' = (Join-Path $managed 'UnityEngine.IMGUIModule.dll')
}
Write-Host "M05 preflight (NO installation): $project" -ForegroundColor Cyan
$details = @(); $missing = @()
foreach ($label in $expectedFiles.Keys) {
    $path = $expectedFiles[$label]
    $exists = Test-Path -LiteralPath $path -PathType Leaf
    if (-not $exists) { $missing += "$label => $path" }
    $hash = if ($exists) { (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() } else { '' }
    $bytes = if ($exists) { (Get-Item -LiteralPath $path).Length } else { 0 }
    [void](Check $label $exists $(if($exists){"found ($bytes bytes)"}else{"missing: $path"}))
    $details += [pscustomobject]@{name=$label;exists=$exists;bytes=$bytes;sha256=$hash;path=$path}
}
if ($missing.Count -gt 0) {
    Write-Host 'The BepInEx archive does not contain UnityEngine DLLs. These must come from the installed WorldBox_Data\Managed folder.' -ForegroundColor Yellow
    throw "Missing dependency. Stop before modifying project. Items: $($missing -join ', ')"
}
$gameHash = ($details | Where-Object name -eq 'WorldBox game assembly').sha256
if ($gameHash -ne $expectedGame) { throw 'WorldBox game DLL fingerprint differs from verified M05 target. STOP; no patch/build/install.' }
[void](Check 'WorldBox verified assembly hash' $true 'matches the uploaded WorldBox 0.51.2 assembly')
$bepHash = ($details | Where-Object name -eq 'BepInEx').sha256
$harmonyHash = ($details | Where-Object name -eq 'Harmony').sha256
if ($bepHash -ne $knownBep -or $harmonyHash -ne $knownHarmony) {
    Write-Warning 'BepInEx/Harmony binaries differ from the uploaded archive. Check version compatibility. Build is not automatically forbidden.'
} else {
    Write-Host 'PASS BepInEx/Harmony fingerprints match uploaded working archive' -ForegroundColor Green
}
if (-not (Test-Path -LiteralPath (Join-Path $plugins 'WorldBoxBridge.dll'))) {
    Write-Warning 'Existing WorldBoxBridge.dll was not found. M05 observer can still be built, but check the game directory.'
} else {
    Write-Host 'PASS existing WorldBoxBridge.dll remains installed (will not be replaced)' -ForegroundColor Green
}
$worldKeyFile = Join-Path $game 'BepInEx\FoundersCIV_M05\world_key.txt'
[void](Check 'M05 world-key file' (Test-Path -LiteralPath $worldKeyFile -PathType Leaf) 'file existence only; value is never copied to diagnostics')
$projFile = Join-Path $project 'bridge\FoundersCIV_M05_Observer.csproj'
if (-not (Test-Path -LiteralPath $projFile -PathType Leaf)) { throw "Missing project $projFile" }
[xml]$xml=Get-Content -LiteralPath $projFile -Raw
$refs=@{}
foreach($ref in $xml.Project.ItemGroup.Reference) {
    if ($null -ne $ref -and $null -ne $ref.Include) { $refs[$ref.Include]=[string]$ref.HintPath }
}
$required = @('BepInEx','0Harmony','UnityEngine','UnityEngine.CoreModule','UnityEngine.IMGUIModule')
$refOk = $true
foreach($r in $required) {
    $correct = $refs.ContainsKey($r) -and $refs[$r] -eq "../build/refs/$r.dll"
    [void](Check "project reference $r" $correct $(if ($refs.ContainsKey($r)) {"declared: $($refs[$r])"} else {'not declared'}))
    if(-not $correct) { $refOk = $false }
}
if ($Repair) {
    $fix = Join-Path $PSScriptRoot 'Repair-M05.ps1'
    Write-Host 'Applying backed-up v0.5.2 reference repair only (no native game changes)...' -ForegroundColor Cyan
    & $fix -ProjectRoot $project -GameDir $game
    if (-not $?) { throw 'Repair-M05 failed' }
    $refOk=$true
}
if (-not $refOk) {
    throw 'M05 references are not v0.5.2 compliant. Re-run with -Repair, then -Build.'
}
$dir = Join-Path $project 'build\diagnostics'
New-Item -ItemType Directory -Path $dir -Force | Out-Null
$report = [pscustomobject]@{
    schema='founders-m05-preflight-v1';
    checked_at_utc=[DateTime]::UtcNow.ToString('o');
    assembly_match=$true;
    no_config_values_or_tokens_collected=$true;
    game_dir=$game;
    project_dir=$project;
    dependencies=$details
}
$report | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath (Join-Path $dir 'preflight.json') -Encoding UTF8
Write-Host "Preflight report (no configuration secrets): $dir\preflight.json" -ForegroundColor Cyan
if ($Build) {
    if (Get-Process -Name 'WorldBox' -ErrorAction SilentlyContinue) { throw 'Close WorldBox before compiling. Build not started.' }
    if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) { throw '.NET SDK missing; check dotnet --version.' }
    Write-Host 'Starting local M05 C# build. This does NOT install any plugin.' -ForegroundColor Cyan
    & (Join-Path $project 'build_bridge.ps1') -GameDir $game
    if(-not $?) { throw 'Build script failed; installation NOT attempted.' }
    $dll=Join-Path $project 'build\Release\FoundersCIV_M05_Observer.dll'
    if(-not (Test-Path -LiteralPath $dll -PathType Leaf)) { throw 'Build DLL missing. Stop; do not install.' }
    Write-Host "BUILD COMPLETED: $dll" -ForegroundColor Green
    Write-Host 'Install only after reviewing the build output with: & "$project\build_bridge.ps1" -GameDir "$game" -Install'
} else {
    Write-Host 'PREFLIGHT COMPLETE. For build, re-run with -Build; no plugin has been installed.' -ForegroundColor Green
}
