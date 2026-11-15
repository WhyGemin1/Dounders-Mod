param(
  [Parameter(Mandatory=$true)][string]$GameDir,
  [switch]$Install
)
$ErrorActionPreference='Stop'
$game=(Resolve-Path $GameDir).Path
$asm=Join-Path $game 'WorldBox_Data\Managed\Assembly-CSharp.dll'
$core=Join-Path $game 'BepInEx\core'
foreach($needed in @($asm,(Join-Path $core 'BepInEx.dll'),(Join-Path $core '0Harmony.dll'),(Join-Path $game 'WorldBox_Data\Managed\UnityEngine.CoreModule.dll'),(Join-Path $game 'WorldBox_Data\Managed\UnityEngine.IMGUIModule.dll'))){
  if(-not (Test-Path -LiteralPath $needed)){throw "Missing required file: $needed"}
}
$expected='51d275f0168be2f6ca26341ab292406714e694e0270eafcb25b999d5df6dd69f'
$actual=(Get-FileHash -Algorithm SHA256 -LiteralPath $asm).Hash.ToLowerInvariant()
if($actual -ne $expected){throw "WorldBox binary mismatch. Expected $expected but got $actual. No changes made."}
if(-not (Get-Command dotnet -ErrorAction SilentlyContinue)){throw 'Install the .NET SDK before building. No changes made.'}
$proj=Join-Path $PSScriptRoot 'bridge\FoundersCIV_M05_Observer.csproj'
$out=Join-Path $PSScriptRoot 'build\Release'
& dotnet build $proj --configuration Release --property:GameDir="$game" --output $out
if($LASTEXITCODE -ne 0){throw 'Build failed. No installation performed.'}
$dll=Join-Path $out 'FoundersCIV_M05_Observer.dll'
if(-not (Test-Path -LiteralPath $dll)){throw 'Build reported success but DLL was missing'}
Write-Host "Build OK: $dll"
if($Install){
  $plugins=Join-Path $game 'BepInEx\plugins'
  New-Item -ItemType Directory -Path $plugins -Force | Out-Null
  $older=Get-ChildItem -Path $plugins -Filter '*M03*Event*.dll' -File -ErrorAction SilentlyContinue
  if($older){throw 'Old M03 observer detected. Disable/move it OUT of BepInEx/plugins and run again to prevent duplicate observation.'}
  $dest=Join-Path $plugins 'FoundersCIV_M05_Observer.dll'
  if(Test-Path $dest){
    $stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
    Copy-Item -LiteralPath $dest -Destination "$dest.$stamp.bak" -Force
  }
  Copy-Item -LiteralPath $dll -Destination $dest -Force
  Write-Host "Installed: $dest"
  Write-Host 'Next: create BepInEx\FoundersCIV_M05\world_key.txt with your save identity BEFORE launching WorldBox.'
}
