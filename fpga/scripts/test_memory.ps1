$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$env:PATH='C:\msys64\ucrt64\bin;'+$env:PATH
Push-Location (Join-Path $root 'sim')
try {
 & iverilog -g2012 -DSIMULATION -s tb_memory -o memory.vvp ../rtl/moonshine_sdram.sv ../rtl/moonshine_memory.sv sdram_model.sv tb_memory.sv
 if($LASTEXITCODE -ne 0){throw 'memory compile failed'}
 & vvp memory.vvp 2>&1 | Tee-Object ../evidence/memory-simulation.log
 if($LASTEXITCODE -ne 0){throw 'memory simulation failed'}
}finally {Pop-Location}
