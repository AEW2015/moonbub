param(
    [string]$TargetDirectory = 'C:\mbt',
    [string]$PythonDirectory = "$env:USERPROFILE\.espressif\python_env\idf5.4_py3.11_env\Scripts",
    [switch]$Package
)
$ErrorActionPreference = 'Stop'
$cargoBin = Join-Path $env:USERPROFILE '.cargo\bin'
$clangBin = Join-Path $env:USERPROFILE '.rustup\toolchains\esp193\xtensa-esp32-elf-clang\esp-clang\bin'
$cmakeBin = Join-Path $env:USERPROFILE '.espressif\tools\cmake\3.30.2\bin'
$ninjaBin = Join-Path $env:USERPROFILE '.espressif\tools\ninja\1.12.1'
foreach ($dependency in @("$cargoBin\cargo.exe", "$clangBin\libclang.dll", "$PythonDirectory\python.exe", "$cmakeBin\cmake.exe", "$ninjaBin\ninja.exe")) {
    if (!(Test-Path -LiteralPath $dependency)) { throw "Missing build dependency: $dependency (see firmware/README.md)" }
}
$env:PATH = "$cargoBin;$clangBin;$PythonDirectory;$cmakeBin;$ninjaBin;$env:PATH"
$env:LIBCLANG_PATH = Join-Path $clangBin 'libclang.dll'
$env:CARGO_TARGET_DIR = $TargetDirectory
$source = Join-Path $PSScriptRoot 'handheld'
$evidence = Join-Path $PSScriptRoot 'evidence'
New-Item -ItemType Directory -Force -Path $evidence | Out-Null
& rustc +stable --edition=2021 --test "$source\src\streaming\protocol.rs" -o "$evidence\protocol-tests.exe"
if ($LASTEXITCODE -ne 0) { throw 'Production protocol test compilation failed' }
& "$evidence\protocol-tests.exe" | Tee-Object -FilePath "$evidence\protocol-tests.log"
if ($LASTEXITCODE -ne 0) { throw 'Production protocol tests failed' }
Push-Location $source
try {
    $ErrorActionPreference = 'Continue'
    & cargo +esp193 build --locked --release --features rev4 2>&1 | ForEach-Object { "$_" } | Tee-Object -FilePath "$evidence\build-rev4-repro.log"
    if ($LASTEXITCODE -ne 0) { throw "Rev4 firmware build failed ($LASTEXITCODE)" }
} finally { Pop-Location }
$ErrorActionPreference = 'Stop'
if ($Package) {
    $release = Join-Path $PSScriptRoot 'release'
    New-Item -ItemType Directory -Force -Path $release | Out-Null
    Copy-Item -LiteralPath "$TargetDirectory\xtensa-esp32s3-espidf\release\handheld" -Destination "$release\moonshine-rev4.elf"
    & "$PythonDirectory\python.exe" -m esptool --chip esp32s3 elf2image --flash_mode dio --flash_freq 80m --flash_size 8MB --output "$release\moonshine-rev4.bin" "$release\moonshine-rev4.elf"
    if ($LASTEXITCODE -ne 0) { throw 'esptool elf2image failed' }
    & "$PythonDirectory\python.exe" -m esptool --chip esp32s3 image_info "$release\moonshine-rev4.bin" | Tee-Object -FilePath "$evidence\image-info.log"
    if ($LASTEXITCODE -ne 0) { throw 'ESP image inspection failed' }
    & "$PythonDirectory\python.exe" "$PSScriptRoot\tools\make_gamebub_uf2.py" "$release\moonshine-rev4.bin" "$release\moonshine-rev4.uf2"
    if ($LASTEXITCODE -ne 0) { throw 'UF2 packaging failed' }
    & rustc +stable --edition=2021 "$PSScriptRoot\tools\verify_uf2.rs" -o "$evidence\verify-uf2.exe"
    if ($LASTEXITCODE -ne 0) { throw 'UF2 verifier build failed' }
    & "$evidence\verify-uf2.exe" "$release\moonshine-rev4.uf2" "$release\moonshine-rev4.bin" | Tee-Object -FilePath "$evidence\uf2-validation.log"
    if ($LASTEXITCODE -ne 0) { throw 'UF2 validation failed' }
    & "$PythonDirectory\python.exe" "$PSScriptRoot\tools\record_build.py" --target $TargetDirectory
    if ($LASTEXITCODE -ne 0) { throw 'Firmware evidence binding failed' }
}
