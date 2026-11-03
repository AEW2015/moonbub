$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$workspace=Split-Path -Parent $root
$out=Join-Path $root 'build-final'
$synthBindings=Get-Content "$root/attempts/v2/source-bindings.json" -Raw | ConvertFrom-Json
foreach($binding in $synthBindings){
 if($binding.path.StartsWith('fpga/rtl/') -or $binding.path.StartsWith('fpga/vendor/')){
  if((Get-FileHash -LiteralPath (Join-Path $workspace $binding.path) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $binding.sha256){throw ('Synthesized RTL changed: '+$binding.path)}
 }
}
$files=@(Get-ChildItem "$root/rtl/*.sv")+@(Get-ChildItem "$root/vendor/core_jpeg/src_v/*.v")+@(Get-ChildItem "$PSScriptRoot/*.tcl")+@(Get-ChildItem "$PSScriptRoot/*.xdc")+@(Get-ChildItem "$root/evidence/*pins_rev4.xdc")+@(Get-Item "$out/synthesized.dcp")
$bindings=@($files | ForEach-Object { @{path=$_.FullName.Substring($workspace.Length+1).Replace('\','/');sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()} })
$bindings | ConvertTo-Json -Depth 4 | Set-Content "$out/source-bindings.json"
Push-Location $workspace
try {
 & C:/Xilinx/2025.2/Vivado/bin/vivado.bat -mode batch -source fpga/scripts/resume_impl.tcl -log fpga/evidence/vivado-final-resume.log -journal fpga/evidence/vivado-final-resume.jou
 if($LASTEXITCODE -ne 0){throw 'FPGA implementation failed; original logs and reports retained'}
 foreach($binding in $bindings){
  if((Get-FileHash -LiteralPath (Join-Path $workspace $binding.path) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $binding.sha256){throw ('Source changed while implementation ran: '+$binding.path)}
 }
}finally{Pop-Location}
