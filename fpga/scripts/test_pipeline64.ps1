$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$env:PATH='C:\msys64\ucrt64\bin;'+$env:PATH
$sources=@('../rtl/moonshine_core.sv','../rtl/moonshine_memory.sv','../rtl/moonshine_sdram.sv')+@(Get-ChildItem "$root/vendor/core_jpeg/src_v/*.v" | ForEach-Object FullName)
Push-Location (Join-Path $root 'sim')
try {
 & iverilog -g2012 -DSIMULATION -s tb_pipeline64 -o pipeline64.vvp @sources sdram_model.sv tb_pipeline64.sv
 if($LASTEXITCODE -ne 0){throw 'pipeline compile failed'}
 & vvp pipeline64.vvp 2>&1 | Tee-Object ../evidence/pipeline64-simulation.log
 if($LASTEXITCODE -ne 0){throw 'pipeline simulation failed'}
}finally {Pop-Location}
