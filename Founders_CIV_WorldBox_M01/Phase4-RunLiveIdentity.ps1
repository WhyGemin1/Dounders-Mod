# Phase 4 — authenticated, read-only WorldBox native actor identity snapshots.
# Does not launch, pause, save or alter WorldBox; user controls gameplay manually.
# Auth token is read from the local BepInEx config and never printed/saved.
[CmdletBinding()]
param(
    [ValidateSet('probe','before','after','compare')][string]$Stage = 'probe',
    [string]$GameDir = 'C:\Program Files (x86)\Steam\steamapps\common\WorldBox',
    [string]$EvidenceDir = "$env:USERPROFILE\Documents\FoundersCIV-Phase4"
)
$ErrorActionPreference = 'Stop'
if (-not (Get-Command 'py' -ErrorAction SilentlyContinue)) {
    throw 'Python launcher py is missing'
}
New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null
$before = Join-Path $EvidenceDir 'M01_before.json'
$after = Join-Path $EvidenceDir 'M01_after.json'
$report = Join-Path $EvidenceDir 'M01_reload_comparison.json'
if ($Stage -eq 'compare') {
    if (-not (Test-Path -LiteralPath $before) -or -not (Test-Path -LiteralPath $after)) {
        throw "Need both real paused snapshot files in $EvidenceDir"
    }
    & py (Join-Path $PSScriptRoot 'compare_live_snapshots.py') $before $after --minimum 20 --output $report
    if ($LASTEXITCODE -ne 0) { throw 'M01 live reload comparison FAILED or incomplete. Do not promote M01.' }
    Write-Host "M01 comparison PASSED as provisional evidence: $report" -ForegroundColor Green
    exit 0
}
if (-not (Get-Process -Name 'WorldBox' -ErrorAction SilentlyContinue)) {
    throw 'Open WorldBox and pause a fully loaded disposable test world first.'
}
$config = Join-Path $GameDir 'BepInEx\config\WorldBoxBridge.cfg'
if (-not (Test-Path -LiteralPath $config -PathType Leaf)) {
    throw "WorldBox-MCP config missing: $config. Build and install M01 bridge first."
}
$original = [Environment]::GetEnvironmentVariable('WORLDBOX_MCP_TOKEN','Process')
try {
    if ([string]::IsNullOrWhiteSpace($original)) {
        $lines = @(Get-Content -LiteralPath $config)
        $tokens = @($lines | Where-Object { $_ -match '^\s*token\s*=\s*\S+\s*$' })
        if ($tokens.Count -ne 1) { throw 'M01 bridge token missing or ambiguous in local config' }
        $token = (($tokens[0] -split '=',2)[1]).Trim().Trim('"')
        if ([string]::IsNullOrWhiteSpace($token)) { throw 'Empty local M01 token' }
        [Environment]::SetEnvironmentVariable('WORLDBOX_MCP_TOKEN',$token,'Process')
    }
    $cli = Join-Path $PSScriptRoot 'm01.py'
    if ($Stage -eq 'probe') {
        & py $cli live-probe
    } elseif ($Stage -eq 'before') {
        & py $cli live-snapshot --output $before
    } else {
        & py $cli live-snapshot --output $after
    }
    if ($LASTEXITCODE -ne 0) { throw 'Live native identity query FAILED; do not substitute names or positions.' }
    if ($Stage -eq 'before') {
        Write-Host "Saved BEFORE snapshot: $before" -ForegroundColor Green
        Write-Host 'Now save and close WorldBox normally, reload the SAME disposable save and PAUSE before running -Stage after.'
    } elseif ($Stage -eq 'after') {
        Write-Host "Saved AFTER snapshot: $after" -ForegroundColor Green
        Write-Host 'Run -Stage compare to check native IDs, species and parent data.'
    }
} finally {
    [Environment]::SetEnvironmentVariable('WORLDBOX_MCP_TOKEN',$original,'Process')
}
