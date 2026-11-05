param(
 [Parameter(Mandatory=$true)][string]$EvidenceDirectory,
 [ValidateSet('check','build')][string]$Action='check',
 [string]$TargetDirectory='C:/mv33src01',
 [string]$CargoBin=(Join-Path $env:USERPROFILE '.cargo/bin'),
 [string]$ClangBin=(Join-Path $env:USERPROFILE '.rustup/toolchains/esp193/xtensa-esp32-elf-clang/esp-clang/bin'),
 [string]$IdfPython=(Join-Path $env:USERPROFILE '.espressif/python_env/idf5.4_py3.11_env/Scripts/python.exe'),
 [string]$IdfDirectory=(Join-Path $env:USERPROFILE '.espressif/esp-idf/v5.4.3'),
 [string]$CmakeBin=(Join-Path $env:USERPROFILE '.espressif/tools/cmake/3.30.2/bin'),
 [string]$NinjaBin=(Join-Path $env:USERPROFILE '.espressif/tools/ninja/1.12.1'),
 [switch]$PreflightOnly
)
$ErrorActionPreference='Stop'; $root=$PSScriptRoot
$ev=[IO.Path]::GetFullPath($EvidenceDirectory); $target=[IO.Path]::GetFullPath($TargetDirectory)
function IsWithin([string]$Child,[string]$Parent) {
 $p=$Parent.TrimEnd([IO.Path]::DirectorySeparatorChar,[IO.Path]::AltDirectorySeparatorChar)
 return $Child.Equals($p,[StringComparison]::OrdinalIgnoreCase) -or $Child.StartsWith($p+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)
}
if(Test-Path -LiteralPath $ev){throw 'Evidence path must be new'}
if($ev.StartsWith($root+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or $ev -eq $root){throw 'Evidence must be outside export'}
if($target.Length -gt 24){throw 'Choose a genuinely short target path (<=24 characters)'}
if(Test-Path -LiteralPath $target){throw 'Target must be a new path'}
if((IsWithin $target $root) -or (IsWithin $root $target)){throw 'Target and export must not overlap'}
if((IsWithin $ev $target) -or (IsWithin $target $ev)){throw 'Evidence and target must not overlap'}
if(IsWithin $root $ev){throw 'Evidence cannot contain the export'}
$required=@((Join-Path $CargoBin 'cargo.exe'),(Join-Path $CargoBin 'rustc.exe'),(Join-Path $CargoBin 'ldproxy.exe'),(Join-Path $ClangBin 'libclang.dll'),$IdfPython,(Join-Path $CmakeBin 'cmake.exe'),(Join-Path $NinjaBin 'ninja.exe'),(Join-Path $IdfDirectory 'tools/idf.py'))
foreach($x in $required){if(!(Test-Path -LiteralPath $x)){throw "Missing external dependency: $x"}}
$env:PATH="$CargoBin;$ClangBin;$(Split-Path $IdfPython);$CmakeBin;$NinjaBin;$env:PATH";$env:LIBCLANG_PATH=Join-Path $ClangBin 'libclang.dll';$env:IDF_PATH=$IdfDirectory;$env:GIT_CEILING_DIRECTORIES=$root
& python (Join-Path $root 'verify_source.py'); if($LASTEXITCODE -ne 0){throw 'Export integrity failed'}
$savedPreference=$ErrorActionPreference; $ErrorActionPreference='Continue'
try { $gitOut=& git -C (Join-Path $root 'handheld') rev-parse HEAD 2>$null; $gitCode=$LASTEXITCODE } finally { $ErrorActionPreference=$savedPreference }
if($gitCode -eq 0){throw 'Git discovery changes selected build identity'}
$rv=& (Join-Path $CargoBin 'rustc.exe') +esp193 -Vv; if($LASTEXITCODE -ne 0 -or ($rv -join "`n") -notmatch '2b43689c53a55786249fe1d7263826eef2d74725'){throw 'Expected esp193 toolchain commit'}
$idf=& $IdfPython (Join-Path $IdfDirectory 'tools/idf.py') --version; if($LASTEXITCODE -ne 0 -or ($idf -join "`n") -notmatch '5\.4\.3'){throw 'Expected ESP-IDF 5.4.3'}
if($PreflightOnly){'PREFLIGHT_PASS; target build NOT RUN'; exit 0}
New-Item -ItemType Directory -Path $ev|Out-Null
@{action=$Action;manifest_sha256=(Get-FileHash (Join-Path $root 'manifest.json') -Algorithm SHA256).Hash.ToLower();target=$target;command="cargo +esp193 $Action --offline --locked --release --features rev4";rustc=$rv -join "`n";idf=$idf -join "`n";hardware='NONE'}|ConvertTo-Json -Depth 4|Set-Content (Join-Path $ev 'invocation.json')
$env:CARGO_TARGET_DIR=$target; Push-Location (Join-Path $root 'handheld')
try { $ErrorActionPreference='Continue'; & (Join-Path $CargoBin 'cargo.exe') +esp193 $Action --offline --locked --release --features rev4 2>&1|ForEach-Object{"$_"}|Tee-Object (Join-Path $ev 'cargo.log');$code=$LASTEXITCODE } finally { Pop-Location }
$ErrorActionPreference='Stop'; & python (Join-Path $root 'verify_source.py'); if($LASTEXITCODE -ne 0){throw 'Export integrity failed after operation'}; if($code -ne 0){throw "Cargo $Action failed"}; 'Cargo operation complete; no runner, flashing or hardware action occurred.'
