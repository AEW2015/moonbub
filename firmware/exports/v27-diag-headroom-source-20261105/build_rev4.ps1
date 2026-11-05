param(
 [Parameter(Mandatory=$true)][string]$EvidenceDirectory,
 [ValidateSet('check','build')][string]$Action='check',
 [string]$TargetDirectory='C:/v27src01',
 [string]$CargoBin=(Join-Path $env:USERPROFILE '.cargo/bin'),
 [string]$ClangBin=(Join-Path $env:USERPROFILE '.rustup/toolchains/esp193/xtensa-esp32-elf-clang/esp-clang/bin'),
 [string]$IdfPython=(Join-Path $env:USERPROFILE '.espressif/python_env/idf5.4_py3.11_env/Scripts/python.exe'),
 [string]$IdfDirectory=(Join-Path $env:USERPROFILE '.espressif/esp-idf/v5.4.3'),
 [string]$CmakeBin=(Join-Path $env:USERPROFILE '.espressif/tools/cmake/3.30.2/bin'),
 [string]$NinjaBin=(Join-Path $env:USERPROFILE '.espressif/tools/ninja/1.12.1'),
 [switch]$PreflightOnly
)
$ErrorActionPreference='Stop'
$packageRoot=$PSScriptRoot
$evidenceRoot=[IO.Path]::GetFullPath($EvidenceDirectory)
if(Test-Path -LiteralPath $evidenceRoot){throw 'Use a new external evidence directory'}
if($evidenceRoot.StartsWith($packageRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or $evidenceRoot -eq $packageRoot){throw 'Evidence must be outside the source export'}
$targetRoot=[IO.Path]::GetFullPath($TargetDirectory)
if($targetRoot.Length -gt 24){throw 'Use a genuinely short fresh target path, e.g.C:/v27src01; no SUBST path'}
if(Test-Path -LiteralPath $targetRoot){throw 'Preserve existing targets; choose a fresh short target directory'}
foreach($tool in @((Join-Path $CargoBin 'cargo.exe'),(Join-Path $CargoBin 'ldproxy.exe'),(Join-Path $ClangBin 'libclang.dll'),$IdfPython,(Join-Path $CmakeBin 'cmake.exe'),(Join-Path $NinjaBin 'ninja.exe'),(Join-Path $IdfDirectory 'tools/idf.py'))){if(!(Test-Path -LiteralPath $tool)){throw "Missing external build dependency: $tool"}}
$env:PATH="$CargoBin;$ClangBin;$(Split-Path $IdfPython);$CmakeBin;$NinjaBin;$env:PATH"
$env:LIBCLANG_PATH=Join-Path $ClangBin 'libclang.dll'
$env:CARGO_TARGET_DIR=$targetRoot
$env:IDF_PATH=$IdfDirectory
$env:GIT_CEILING_DIRECTORIES=$packageRoot
& python (Join-Path $packageRoot 'verify_source.py');if($LASTEXITCODE -ne 0){throw 'Source integrity failed'}
$ErrorActionPreference='Continue'
$gitResult=& git -C (Join-Path $packageRoot 'handheld') rev-parse HEAD 2>&1
$gitCode=$LASTEXITCODE
$ErrorActionPreference='Stop'
if($gitCode -eq 0){throw 'Git discovery would alter selectedGIT_COMMIT; use a source directory below the configured discovery ceiling'}
$rustVersion=& (Join-Path $CargoBin 'rustc.exe') +esp193 -Vv
if($LASTEXITCODE -ne 0 -or ($rustVersion -join "`n") -notmatch '2b43689c53a55786249fe1d7263826eef2d74725'){throw 'Expected esp193 rustc1.93.0.0 commit2b43689c5'}
$idfVersion=& $IdfPython (Join-Path $IdfDirectory 'tools/idf.py') --version
if($LASTEXITCODE -ne 0 -or ($idfVersion -join "`n") -notmatch '5\.4\.3'){throw 'Expected ESP-IDF5.4.3'}
if($PreflightOnly){Write-Output "PREFLIGHT_ONLY_PASS; source/Gitfallback/tool versions checked; targetbuild NOT_RUN";exit 0}
$logRoot=$evidenceRoot
if(Test-Path -LiteralPath $logRoot){throw 'Preserve previous build evidence; use a fresh export directory'}
New-Item -ItemType Directory -Path $logRoot | Out-Null
@{action=$Action;source=(Join-Path $packageRoot 'handheld');target=$targetRoot;command="cargo +esp193 $Action --offline --locked --release --features rev4";rustc=($rustVersion -join "`n");idf=($idfVersion -join "`n");git_identity='selected unchanged build.rs fallback aa281c073693bd92850720a2e43998f1d8faf569';hardware='NONE'}|ConvertTo-Json -Depth 4|Set-Content -LiteralPath (Join-Path $logRoot 'invocation.json')
Push-Location (Join-Path $packageRoot 'handheld')
try {
 $ErrorActionPreference='Continue'
 & (Join-Path $CargoBin 'cargo.exe') +esp193 $Action --offline --locked --release --features rev4 2>&1|ForEach-Object{"$_"}|Tee-Object -FilePath (Join-Path $logRoot 'cargo.log')
 $targetResult=$LASTEXITCODE
} finally {Pop-Location}
$ErrorActionPreference='Stop'
& python (Join-Path $packageRoot 'verify_source.py');if($LASTEXITCODE -ne 0){throw 'Sources changed during target operation'}
if($targetResult -ne 0){throw "Target $Action failed; original sources/evidence preserved"}
Write-Output 'Target operation complete; no run/flash/USB/COM/JTAG/SD action occurred.'
