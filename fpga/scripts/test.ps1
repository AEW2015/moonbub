$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$env:PATH='C:\msys64\ucrt64\bin;'+$env:PATH
$out=Join-Path $root 'sim'
$sources=@((Join-Path $root 'rtl/moonshine_core.sv'))+@(Get-ChildItem "$root/vendor/core_jpeg/src_v/*.v" | ForEach-Object FullName)
Push-Location $out
try {
 & iverilog -g2012 -s tb_core -o core.vvp @sources tb_core.sv 2>&1 | Tee-Object compile.log
 if($LASTEXITCODE -ne 0){throw 'iverilog failed'}
 & vvp core.vvp 2>&1 | Tee-Object core.log
 if($LASTEXITCODE -ne 0){throw 'core simulation failed'}
} finally {Pop-Location}
