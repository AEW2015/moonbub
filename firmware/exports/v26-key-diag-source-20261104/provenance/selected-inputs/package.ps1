param([string]$Stage = '03', [string]$ReleaseName = 'release-key-resource')
$ErrorActionPreference = 'Stop'
$python = Join-Path $env:USERPROFILE '.espressif\python_env\idf5.4_py3.11_env\Scripts\python.exe'
$rustc = Join-Path $env:USERPROFILE '.cargo\bin\rustc.exe'
$evidence = Join-Path $PSScriptRoot 'evidence'
$release = Join-Path $PSScriptRoot $ReleaseName
if (Test-Path -LiteralPath $release) { throw 'Release directory already exists; preserve prior package' }
New-Item -ItemType Directory -Path $release | Out-Null
Copy-Item -LiteralPath "$evidence\v26-key-diag-access-rev4-$Stage.elf" -Destination "$release\moonshine-rev4.elf"
& $python -m esptool --chip esp32s3 elf2image --flash_mode dio --flash_freq 80m --flash_size 8MB --output "$release\moonshine-rev4.bin" "$release\moonshine-rev4.elf" 2>&1 | ForEach-Object { "$_" } | Tee-Object "$evidence\elf2image.log"
if ($LASTEXITCODE -ne 0) { throw 'elf2image failed' }
& $python -m esptool --chip esp32s3 image_info "$release\moonshine-rev4.bin" 2>&1 | ForEach-Object { "$_" } | Tee-Object "$evidence\image-info.log"
if ($LASTEXITCODE -ne 0) { throw 'image_info failed' }
& $python "$PSScriptRoot\tools\make_gamebub_uf2.py" "$release\moonshine-rev4.bin" "$release\moonshine-rev4.uf2" | Tee-Object "$evidence\uf2-package.log"
if ($LASTEXITCODE -ne 0) { throw 'UF2 packaging failed' }
& $rustc +stable --edition=2021 "$PSScriptRoot\tools\verify_uf2.rs" -o "$evidence\verify-uf2.exe"
if ($LASTEXITCODE -ne 0) { throw 'UF2 verifier compilation failed' }
& "$evidence\verify-uf2.exe" "$release\moonshine-rev4.uf2" "$release\moonshine-rev4.bin" | Tee-Object "$evidence\uf2-validation.log"
if ($LASTEXITCODE -ne 0) { throw 'Production updater validation failed' }
