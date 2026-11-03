$ErrorActionPreference='Stop'
$workspaceRoot=Split-Path -Parent $PSScriptRoot
$env:PATH='C:\msys64\ucrt64\bin;'+$env:PATH
Push-Location $workspaceRoot
try {
    & iverilog -g2012 -s tb_esp32_overlay -o fpga/evidence/overlay-test.vvp fpga/rtl/esp32_overlay.sv fpga/sim/tb_esp32_overlay.sv
    if($LASTEXITCODE -ne 0){throw 'Overlay compile failed'}
    & vvp fpga/evidence/overlay-test.vvp | Tee-Object -FilePath fpga/evidence/overlay-simulation.log
    if($LASTEXITCODE -ne 0){throw 'Overlay simulation failed'}
    if(-not(Select-String -LiteralPath fpga/evidence/overlay-simulation.log -Pattern '^ESP32_OVERLAY_PASS ' -Quiet)){throw 'Overlay checks did not finish'}
} finally {Pop-Location}
