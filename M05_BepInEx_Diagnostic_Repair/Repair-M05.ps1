# Patch a working M05 Python sidecar WITHOUT replacing its sqlite database,
# local_world.json, native WorldBox game assembly, save, or existing bridge DLL.
param(
    [string]$ProjectRoot = 'C:\Dev\FoundersCIV_WorldBox_M05_Integration',
    [string]$GameDir = 'C:\Program Files (x86)\Steam\steamapps\common\WorldBox',
    [switch]$Build
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $ProjectRoot -ErrorAction Stop).Path
$payload = Join-Path $PSScriptRoot 'payload'
$existing = Join-Path $root 'm05.py'
if (-not (Test-Path -LiteralPath $existing -PathType Leaf)) {
    throw "Existing M05 folder not recognized: $root. No changes made."
}
$targets = @(
    'bridge\FoundersCIV_M05_Observer.csproj',
    'bridge\FoundersCIV_M05_Observer.cs',
    'build_bridge.ps1'
)
foreach ($relative in $targets) {
    if (-not (Test-Path -LiteralPath (Join-Path $payload $relative) -PathType Leaf)) {
        throw "Repair ZIP incomplete: missing payload/$relative. No changes made."
    }
    if (-not (Test-Path -LiteralPath (Join-Path $root $relative) -PathType Leaf)) {
        throw "Existing M05 source file missing: $relative. No changes made."
    }
}
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backup = Join-Path $root "M05_052_backup_$stamp"
New-Item -ItemType Directory -Path $backup -Force | Out-Null
foreach ($relative in $targets) {
    $before = Join-Path $root $relative
    $backupPath = Join-Path $backup $relative
    $backupFolder = Split-Path -Parent $backupPath
    New-Item -ItemType Directory -Path $backupFolder -Force | Out-Null
    Copy-Item -LiteralPath $before -Destination $backupPath -Force
}
Write-Host "Backed up original build files to: $backup"
foreach ($relative in $targets) {
    $from = Join-Path $payload $relative
    $to = Join-Path $root $relative
    Copy-Item -LiteralPath $from -Destination $to -Force
    $sha1 = (Get-FileHash -LiteralPath $from -Algorithm SHA256).Hash
    $sha2 = (Get-FileHash -LiteralPath $to -Algorithm SHA256).Hash
    if ($sha1 -ne $sha2) { throw "Patch copy verification failed: $relative. Restore backup in $backup." }
    Write-Host "  Patched and verified: $relative"
}
Write-Host 'Your data\ folder, local_world.json and game files were NOT changed.' -ForegroundColor Green
Write-Host 'The old compiled DLL was NOT installed or replaced.'

if ($Build) {
    Write-Host 'Running a clean, build-only compile; no installation...' -ForegroundColor Cyan
    & (Join-Path $root 'build_bridge.ps1') -GameDir $GameDir
    Write-Host 'M05.2 repair + local build completed. Install separately after checking results.' -ForegroundColor Green
}
