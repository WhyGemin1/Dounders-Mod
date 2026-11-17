# U026 C043: Windows PowerShell acceptance tests. Synthetic event fixtures ONLY.
# No WorldBox launch, no installed DLL, no user save modification.
$ErrorActionPreference = 'Stop'
$validator = Join-Path (Split-Path $PSScriptRoot -Parent) 'Phase3-CheckEvents.ps1'
$root = Join-Path $env:TEMP ("U026-M05-C043-" + [guid]::NewGuid().ToString('N'))
$eventDir = Join-Path $root 'BepInEx\FoundersCIV_M05'
New-Item -ItemType Directory -Path $eventDir -Force | Out-Null
$path = Join-Path $eventDir 'm05_fixture.jsonl'
$expected = '51d275f0168be2f6ca26341ab292406714e694e0270eafcb25b999d5df6dd69f'
$hooks = @(
 'Actor.addNutritionFromEating', 'ai.behaviours.BehConsumeActorTarget.consume',
 'Actor.consumeFoodResource', 'Actor.newKillAction', 'Actor.die',
 'ActorManager.createBabyActorFromData', 'Actor.birthEvent'
)
$casesRun = 0
function New-Events {
  $common = @{schema=1;session_id='fixture-session';world_key='copied-test-save'}
  $a = @()
  foreach ($n in 1..4) {
    $row = @{} + $common
    $row.seq = $n
    $row.kind = @('session_open','observer_heartbeat','nutrition_call','session_close')[$n-1]
    $row.notes = ''
    $a += ,$row
  }
  $a[0].assembly_sha256 = $script:expected
  $a[0].active_hooks = @($script:hooks)
  $a[2].native_success = $true
  $a[3].notes = 'update_frames=1;hook_hits=nutrition=1;callback_errors=0;emit_errors=0'
  return ,$a
}
function Run-Case([string]$Name, [bool]$ShouldPass) {
  $events = New-Events
  switch ($Name) {
    'good' { }
    'seq_gap' { $events[2].seq = 9 }
    'duplicate_seq' { $events[2].seq = 2 }
    'missing_close' { $events = @($events[0],$events[1],$events[2]) }
    'bridge_loss' { $events[2].kind = 'bridge_loss'; $events[2].dropped = 1 }
    'observer_disabled' { $events[2].kind = 'observer_disabled' }
    'missing_hook' { $events[0].active_hooks = @($script:hooks[0..5]) }
    'wrong_assembly' { $events[0].assembly_sha256 = 'wrong' }
    'no_behavior' { $events[2].kind = 'hook_probe' }
    'no_heartbeat' { $events[1].kind = 'hook_probe' }
    'unbound' { foreach ($item in $events) { $item.world_key = 'UNBOUND' } }
    'mixed_session' { $events[2].session_id = 'other' }
    'callback_error' { $events[3].notes = 'callback_errors=1;emit_errors=0' }
    'emit_error' { $events[3].notes = 'callback_errors=0;emit_errors=1' }
    'wrong_schema' { $events[1].schema = 9 }
    'duplicate_open' { $events[1].kind = 'session_open' }
    default { throw "Unknown fixture $Name" }
  }
  $lines = [string[]]@($events | ForEach-Object { $_ | ConvertTo-Json -Depth 8 -Compress })
  [System.IO.File]::WriteAllLines($script:path, $lines,
    (New-Object System.Text.UTF8Encoding($false)))
  $passed = $true
  try { & $script:validator -GameDir $script:root *> $null }
  catch { $passed = $false }
  if ($passed -ne $ShouldPass) {
    throw "Fixture $Name expected PASS=$ShouldPass, actual PASS=$passed"
  }
  $script:casesRun++
  Write-Host "C043 $Name expected=$ShouldPass verified"
}
try {
  Run-Case 'good' $true
  foreach ($bad in @('seq_gap','duplicate_seq','missing_close','bridge_loss',
    'observer_disabled','missing_hook','wrong_assembly','no_behavior','no_heartbeat','unbound',
    'mixed_session','callback_error','emit_error','wrong_schema','duplicate_open')) {
      Run-Case $bad $false
  }
  if ($casesRun -ne 16) { throw "Expected 16 fixtures, got $casesRun" }
  Write-Host "M05 C046 capture acceptance: $casesRun/16 fixtures PASS" -ForegroundColor Green
}
finally {
  Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}
