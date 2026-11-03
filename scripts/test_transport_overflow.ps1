$ErrorActionPreference='Stop'
$workspaceRoot=Split-Path -Parent $PSScriptRoot
$env:PATH='C:\msys64\ucrt64\bin;'+$env:PATH
Push-Location $workspaceRoot
try {
    & iverilog -g2012 -s tb_transport_overflow -o fpga/evidence/transport-test.vvp fpga/rtl/moonshine_bus_cdc.sv fpga/sim/tb_transport_overflow.sv
    if($LASTEXITCODE -ne 0){throw 'Transport overflow compile failed'}
    & vvp fpga/evidence/transport-test.vvp | Tee-Object -FilePath fpga/evidence/transport-overflow.log
    if($LASTEXITCODE -ne 0){throw 'Transport overflow simulation failed'}
    if(-not(Select-String -LiteralPath fpga/evidence/transport-overflow.log -Pattern '^TRANSPORT_OVERFLOW_PASS ' -Quiet)){throw 'Transport overflow checks did not finish'}
} finally {Pop-Location}
