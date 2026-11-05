param(
    [ValidateSet('check','build')][string]$Action = 'check',
    [string]$Stage = '01',
    [string]$TargetDirectory = 'C:\mv26'
)
$ErrorActionPreference = 'Stop'
$cargoBin = Join-Path $env:USERPROFILE '.cargo\bin'
$clangBin = Join-Path $env:USERPROFILE '.rustup\toolchains\esp193\xtensa-esp32-elf-clang\esp-clang\bin'
$pythonBin = Join-Path $env:USERPROFILE '.espressif\python_env\idf5.4_py3.11_env\Scripts'
$cmakeBin = Join-Path $env:USERPROFILE '.espressif\tools\cmake\3.30.2\bin'
$ninjaBin = Join-Path $env:USERPROFILE '.espressif\tools\ninja\1.12.1'
$env:PATH = "$cargoBin;$clangBin;$pythonBin;$cmakeBin;$ninjaBin;$env:PATH"
$env:LIBCLANG_PATH = Join-Path $clangBin 'libclang.dll'
$env:CARGO_TARGET_DIR = $TargetDirectory
$evidence = Join-Path $PSScriptRoot 'evidence'
$snapshot = Join-Path $evidence "prebuild-$Stage\snapshot.json"
$binding = Get-Content -LiteralPath $snapshot -Raw | ConvertFrom-Json
foreach ($entry in $binding.files.PSObject.Properties) {
    $path = Join-Path $PSScriptRoot $entry.Name
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value) { throw "Prebuild input changed: $($entry.Name)" }
}
$log = Join-Path $evidence "target-$Action-$Stage.log"
if (Test-Path -LiteralPath $log) { throw "Preserving previous target log $log" }
@{ start_utc = [DateTime]::UtcNow.ToString('o'); source = (Join-Path $PSScriptRoot 'handheld'); snapshot_sha256 = (Get-FileHash -LiteralPath $snapshot -Algorithm SHA256).Hash.ToLowerInvariant(); target = $TargetDirectory; action = $Action; command = "cargo +esp193 $Action --offline --locked --release --features rev4" } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $evidence "target-$Action-$Stage-invocation.json") -Encoding UTF8
Push-Location (Join-Path $PSScriptRoot 'handheld')
try {
    $ErrorActionPreference = 'Continue'
    & cargo +esp193 $Action --offline --locked --release --features rev4 2>&1 | ForEach-Object { "$_" } | Tee-Object -FilePath $log
    $resultCode = $LASTEXITCODE
} finally { Pop-Location }
$ErrorActionPreference = 'Stop'
if ($resultCode -ne 0) { throw "Rev4 $Action failed ($resultCode); original log retained" }
foreach ($entry in $binding.files.PSObject.Properties) {
    $path = Join-Path $PSScriptRoot $entry.Name
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value) { throw "Prebuild input changed during $Action : $($entry.Name)" }
}
if ($Action -eq 'build') {
    Copy-Item -LiteralPath "$TargetDirectory\xtensa-esp32s3-espidf\release\handheld" -Destination "$evidence\v26-key-diag-access-rev4-$Stage.elf"
}
Write-Output "Offline target $Action complete; no device action performed."
