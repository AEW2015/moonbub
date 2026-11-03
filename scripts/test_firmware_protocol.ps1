$ErrorActionPreference='Stop'
$workspaceRoot=Split-Path -Parent $PSScriptRoot
Push-Location $workspaceRoot
try {
    & "$env:USERPROFILE\.cargo\bin\rustc.exe" +stable --edition=2021 --test firmware/handheld/src/streaming/protocol.rs -o firmware/evidence/protocol-tests.exe
    if($LASTEXITCODE -ne 0){throw 'Firmware protocol test compile failed'}
    & .\firmware\evidence\protocol-tests.exe | Tee-Object -FilePath firmware/evidence/protocol-tests.log
    if($LASTEXITCODE -ne 0){throw 'Firmware protocol tests failed'}
} finally {Pop-Location}
