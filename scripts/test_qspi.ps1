param([double]$StartPhaseNs=0.0)
$ErrorActionPreference='Stop'
$workspaceRoot=Split-Path -Parent $PSScriptRoot
$env:PATH='C:\msys64\ucrt64\bin;'+$env:PATH
Push-Location $workspaceRoot
try {
    & C:\msys64\ucrt64\bin\iverilog.exe -g2012 "-Pmoonshine_qspi_cdc_tb.START_PHASE_NS=$StartPhaseNs" -s moonshine_qspi_cdc_tb -o fpga/evidence/qspi-test.vvp fpga/rtl/moonshine_qspi_endpoint.sv fpga/rtl/moonshine_bus_cdc.sv fpga/sim/moonshine_qspi_cdc_tb.sv
    if($LASTEXITCODE -ne 0){throw 'QSPI compile failed'}
    & C:\msys64\ucrt64\bin\vvp.exe fpga/evidence/qspi-test.vvp | Tee-Object -FilePath fpga/evidence/qspi-simulation.log
    if($LASTEXITCODE -ne 0){throw 'QSPI simulation failed'}
    if(-not(Select-String -LiteralPath fpga/evidence/qspi-simulation.log -Pattern '^QSPI_CDC_PASS ' -Quiet)){throw 'QSPI checks did not finish'}
    $sourceHashes=@{}
    foreach($file in @('fpga/rtl/moonshine_qspi_endpoint.sv','fpga/rtl/moonshine_bus_cdc.sv','fpga/sim/moonshine_qspi_cdc_tb.sv')){
        $sourceHashes[$file]=(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    @{status='pass';phase_ns=$StartPhaseNs;sources=$sourceHashes;evidence='fpga/evidence/qspi-simulation.log'} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath fpga/evidence/qspi-result.json
} finally { Pop-Location }
