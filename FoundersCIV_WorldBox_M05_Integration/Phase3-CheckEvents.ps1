# M05 U026-C043: fail-closed verification of ONE closed, bound native observation session.
# Read-only. A passing capture is NOT evidence of ecological stability or proof
# that callback success means animal feeding, predation, reproduction or death.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$GameDir)
$ErrorActionPreference = 'Stop'
$expectedAssembly = '51d275f0168be2f6ca26341ab292406714e694e0270eafcb25b999d5df6dd69f'
$requiredHooks = @(
    'Actor.addNutritionFromEating', 'ai.behaviours.BehConsumeActorTarget.consume',
    'Actor.consumeFoodResource', 'Actor.newKillAction', 'Actor.die',
    'ActorManager.createBabyActorFromData', 'Actor.birthEvent'
)
$behaviorKinds = @(
    'nutrition_call', 'resource_consume_call', 'prey_consume_attempt',
    'prey_consume_end', 'kill_callback', 'death_callback',
    'baby_factory_call', 'birth_callback'
)
$game = (Resolve-Path -LiteralPath $GameDir -ErrorAction Stop).Path
$dir = Join-Path $game 'BepInEx\FoundersCIV_M05'
if (-not (Test-Path -LiteralPath $dir -PathType Container)) {
    throw "Observer directory missing: $dir"
}
$file = Get-ChildItem -LiteralPath $dir -Filter 'm05_*.jsonl' -File |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $file) { throw "No M05 session found in $dir" }

# Stream records rather than loading an unbounded game-session log into RAM.
$counts = @{}
$failures = New-Object 'System.Collections.Generic.List[string]'
$index = [long]0
$expectedSeq = [long]1
$sessionId = $null
$worldKey = $null
$opening = $null
$closing = $null
$lastKind = $null
$firstKind = $null
$heartbeatCount = 0
$behaviorCount = 0
$reader = New-Object System.IO.StreamReader($file.FullName)
try {
while ($null -ne ($line = $reader.ReadLine())) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $index++
    try { $ev = $line | ConvertFrom-Json -ErrorAction Stop }
    catch {
        $failures.Add("Malformed JSON at event $index")
        break
    }
    if ($null -eq $ev -or $ev.schema -ne 1) {
        $failures.Add("Invalid schema at event $index")
        break
    }
    $kind = [string]$ev.kind
    if (-not $kind) { $failures.Add("Missing event kind at event $index"); break }
    if ($null -eq $firstKind) { $firstKind = $kind }
    $lastKind = $kind
    if (-not $counts.ContainsKey($kind)) { $counts[$kind] = 0 }
    $counts[$kind]++
    $id = [string]$ev.session_id
    $key = [string]$ev.world_key
    if ([string]::IsNullOrWhiteSpace($id) -or [string]::IsNullOrWhiteSpace($key) -or $key -eq 'UNBOUND') {
        $failures.Add("Missing/unbound session or world identity at event $index")
        break
    }
    if ($null -eq $sessionId) { $sessionId = $id; $worldKey = $key }
    if ($id -ne $sessionId -or $key -ne $worldKey) {
        $failures.Add("Mixed world/session identity at event $index")
        break
    }
    try { $seq = [long]$ev.seq }
    catch { $failures.Add("Invalid sequence at event $index"); break }
    if ($seq -ne $expectedSeq) {
        $failures.Add("Sequence gap or duplicate at event $index (expected $expectedSeq, got $seq)")
        break
    }
    $expectedSeq = $seq + 1
    if ($kind -eq 'bridge_loss') {
        $failures.Add("Bridge dropped events; capture cannot be promoted")
        break
    }
    if ($kind -eq 'observer_disabled') {
        $failures.Add("Observer disabled during capture; session cannot certify hook coverage")
        break
    }
    if ($kind -eq 'session_open') {
        if ($null -ne $opening) { $failures.Add("Duplicate session_open"); break }
        $opening = $ev
    }
    if ($kind -eq 'session_close') {
        if ($null -ne $closing) { $failures.Add("Duplicate session_close"); break }
        $closing = $ev
    }
    if ($kind -eq 'observer_heartbeat') { $heartbeatCount++ }
    if ($behaviorKinds -contains $kind) { $behaviorCount++ }
}
} finally {
    # Windows locks an open game log; release even when rejecting early.
    $reader.Dispose()
}
if ($index -eq 0) { $failures.Add("Session log empty") }
if ($firstKind -ne 'session_open' -or $null -eq $opening) {
    $failures.Add("Missing first session_open")
}
if ($lastKind -ne 'session_close' -or $null -eq $closing) {
    $failures.Add("Missing final session_close; game may not have shut down cleanly")
}
if ($null -ne $opening) {
    if ([string]$opening.assembly_sha256 -ne $expectedAssembly) {
        $failures.Add("WorldBox assembly SHA mismatch or missing: native hooks unverified")
    }
    $installedHooks = @($opening.active_hooks)
    foreach ($hook in $requiredHooks) {
        if ($installedHooks -notcontains $hook) { $failures.Add("Native hook not attached: $hook") }
    }
    if ($installedHooks.Count -ne $requiredHooks.Count) {
        $failures.Add("Unexpected native hook count")
    }
}
if ($heartbeatCount -lt 1) { $failures.Add("No Update heartbeat; observer lifecycle unverified") }
if ($behaviorCount -lt 1) { $failures.Add("No animal-behavior callbacks; probes do not count") }
if ($null -ne $closing) {
    foreach ($counter in @('callback_errors', 'emit_errors')) {
        $match = [regex]::Match([string]$closing.notes, "(?:^|;)$counter=(\d+)")
        if (-not $match.Success -or [long]$match.Groups[1].Value -ne 0) {
            $failures.Add("Missing or nonzero $counter in close diagnostics")
        }
    }
}
Write-Host "M05 capture: $($file.Name) | events $index | world $worldKey | session $sessionId"
foreach ($kind in ($counts.Keys | Sort-Object)) {
    Write-Host ("  {0,-26} {1,8}" -f $kind, $counts[$kind])
}
if ($failures.Count -gt 0) {
    foreach ($reason in $failures) { Write-Error "CAPTURE REJECTED: $reason" -ErrorAction Continue }
    throw "M05 capture FAIL: $($failures.Count) integrity/behavior gate(s) failed"
}
Write-Host "M05 CAPTURE PASS: closed, bound, gap-free record; $behaviorCount callback(s); 7 required hooks." -ForegroundColor Green
Write-Host "READ-ONLY: observed callbacks alone do not establish animal physiology or native gameplay correctness."
