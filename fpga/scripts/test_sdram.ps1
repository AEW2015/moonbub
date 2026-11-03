$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$env:PATH='C:\msys64\ucrt64\bin;'+$env:PATH
Push-Location (Join-Path $root 'sim')
try {
 $logPath=[IO.Path]::GetFullPath((Join-Path (Get-Location) '../evidence/sdram-simulation.log'))
 $logLines=New-Object 'System.Collections.Generic.List[string]'
 $utf8=New-Object System.Text.UTF8Encoding($false)
 $logLines.Add('Functional SDRAM read-clock phase279deg, model forwarded-clock pad flight4ns')
 [IO.File]::WriteAllLines($logPath,$logLines,$utf8)
 foreach($tac in @(2,7)){
  & iverilog -g2012 -DSIMULATION "-Ptb_sdram.T_AC_NS=$tac" -s tb_sdram -o sdram.vvp ../rtl/moonshine_sdram.sv tb_sdram.sv
  if($LASTEXITCODE -ne 0){throw 'SDRAM compile failed'}
  $logLines.Add("T_AC_NS=$tac")
  Write-Output "T_AC_NS=$tac"
  $simulationOutput=@(& vvp sdram.vvp +wave 2>&1 | ForEach-Object { "$_" })
  $simulationExit=$LASTEXITCODE
  foreach($line in $simulationOutput){$logLines.Add($line);Write-Output $line}
  [IO.File]::WriteAllLines($logPath,$logLines,$utf8)
  if($simulationExit -ne 0){throw 'SDRAM simulation failed'}
 }
}finally {Pop-Location}
