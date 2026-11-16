# M05.4 native capture diagnostic: read-only report for the newest closed session.
# Does not manipulate WorldBox or Core151 and never treats probes as animal behavior.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$GameDir
)
$ErrorActionPreference = 'Stop'
$game = (Resolve-Path -LiteralPath $GameDir -ErrorAction Stop).Path
$dir = Join-Path $game 'BepInEx\FoundersCIV_M05'
if (-not (Test-Path -LiteralPath $dir)) { throw "Missing M05 observer directory: $dir" }
$file = Get-ChildItem -LiteralPath $dir -Filter 'm05_*.jsonl' -File |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $file) { throw "No real M05 observation files found in $dir" }
$events = @(Get-Content -LiteralPath $file.FullName | Where-Object { $_.Trim() } |
    ForEach-Object { $_ | ConvertFrom-Json })
if ($events.Count -eq 0) { throw "Observer log exists but is empty: $($file.FullName)" }
Write-Host "Observer file: $($file.Name) | bytes: $($file.Length) | JSON events: $($events.Count)"
$events | Group-Object kind | Sort-Object Name | ForEach-Object {
    Write-Host ("  {0,-26} {1,6}" -f $_.Name,$_.Count)
}
$opens = @($events | Where-Object { $_.kind -eq 'session_open' })
$closes = @($events | Where-Object { $_.kind -eq 'session_close' })
$heartbeats = @($events | Where-Object { $_.kind -eq 'observer_heartbeat' })
$probes = @($events | Where-Object { $_.kind -eq 'hook_probe' })
$behaviorKinds = @('nutrition_call','resource_consume_call','prey_consume_attempt',
                   'prey_consume_end','kill_callback','death_callback',
                   'baby_factory_call','birth_callback')
$behaviors = @($events | Where-Object { $behaviorKinds -contains $_.kind })
if ($opens.Count -ne 1 -or $closes.Count -ne 1) {
    Write-Warning 'Session boundary incomplete; use a normal game shutdown and rerun.'
}
$probes | Select-Object kind,source_method,notes | Format-Table -AutoSize
if ($heartbeats.Count) {
    Write-Host "Last live heartbeat: $($heartbeats[-1].notes)"
} else { Write-Warning 'No M05.4 heartbeat. Check installed DLL version and observer Update lifecycle.' }
if ($closes.Count) { Write-Host "Close summary: $($closes[-1].notes)" }
if ($behaviors.Count -eq 0) {
    Write-Warning 'FAIL: No real animal behavior callbacks in the selected session.'
    Write-Host 'Use heartbeat hook_hits to distinguish unused native targets from callback failures.'
    exit 2
}
Write-Host "PASS: $($behaviors.Count) native behavioral callback event(s) were recorded." -ForegroundColor Green
Write-Host 'These are observed callbacks only; birth and kill events still require semantic validation.'
