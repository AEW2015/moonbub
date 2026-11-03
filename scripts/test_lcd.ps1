$ErrorActionPreference='Stop'
$workspaceRoot=Split-Path -Parent $PSScriptRoot
$env:PATH='C:\msys64\ucrt64\bin;'+$env:PATH
Push-Location $workspaceRoot
try {
    & C:\msys64\ucrt64\bin\iverilog.exe -g2012 -s moonshine_lcd_tb -o fpga/evidence/lcd-test.vvp fpga/rtl/moonshine_lcd.sv fpga/sim/moonshine_lcd_tb.sv
    if($LASTEXITCODE -ne 0){throw 'LCD compile failed'}
    & C:\msys64\ucrt64\bin\vvp.exe fpga/evidence/lcd-test.vvp | Tee-Object -FilePath fpga/evidence/lcd-simulation.log
    if($LASTEXITCODE -ne 0){throw 'LCD simulation failed'}
    if(-not(Select-String -LiteralPath fpga/evidence/lcd-simulation.log -Pattern '^LCD_PASS ' -Quiet)){throw 'LCD checks did not finish'}
    $sourceHashes=@{}
    foreach($file in @('fpga/rtl/moonshine_lcd.sv','fpga/sim/moonshine_lcd_tb.sv')){
        $sourceHashes[$file]=(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    @{status='pass';sources=$sourceHashes;evidence='fpga/evidence/lcd-simulation.log'} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath fpga/evidence/lcd-result.json
} finally { Pop-Location }
