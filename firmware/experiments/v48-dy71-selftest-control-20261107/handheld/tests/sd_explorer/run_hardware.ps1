param(
 [Parameter(Mandatory)][ValidateSet('Program','Test')][string]$Mode,
 [string]$Bitfile='C:\xup\bub\gamebub_sd_explorer_v4\release\gamebub-sd-explorer-rev4.1.bit',
 [string]$ExpectedPreviousUserId='B0100004',
 [string]$FixtureRoot=(Join-Path $PSScriptRoot 'GBTEST\integration-001'),
 [string]$ResultsDirectory=(Join-Path $PSScriptRoot ('results\'+[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')))
)
$ErrorActionPreference='Stop'
if(Test-Path -LiteralPath $ResultsDirectory){throw 'Use a fresh results directory'}
New-Item -ItemType Directory -Path $ResultsDirectory|Out-Null
$tcl=Join-Path $PSScriptRoot 'run_hardware.tcl'
$output=& 'C:\Xilinx\2025.2\Vivado\bin\vivado.bat' -mode batch -source $tcl -tclargs $Mode.ToLowerInvariant() ([IO.Path]::GetFullPath($Bitfile)) $ExpectedPreviousUserId 2>&1 | Tee-Object -FilePath (Join-Path $ResultsDirectory "$($Mode.ToLowerInvariant()).log")
if($LASTEXITCODE){throw "Vivado hardware $Mode failed"}
if($Mode -eq 'Test'){
 $text=$output -join "`n"
 if($text -notmatch 'read_name=([^ ]+) read_bytes=([0-9]+) read_fnv=([0-9A-Fa-f]{8})'){throw 'Missing CPU read proof'}
 $readName=$Matches[1];$readLength=[int]$Matches[2];$readHash=$Matches[3].ToUpperInvariant()
 $file=Join-Path (Resolve-Path $FixtureRoot) ('many\'+$readName.ToLowerInvariant())
 $bytes=[IO.File]::ReadAllBytes($file);[uint32]$hash=2166136261
 foreach($byte in $bytes){$hash=[uint32](([uint64]($hash -bxor $byte)*16777619)-band 0xffffffff)}
 if($bytes.Length -ne $readLength -or ('{0:X8}' -f $hash) -ne $readHash){throw 'CPU-consumed file data differs from the PC fixture'}
 "SD_EXPLORER_PC_COMPARE_PASS file=$file bytes=$($bytes.Length) fnv=$('{0:X8}' -f $hash)"|Tee-Object -FilePath (Join-Path $ResultsDirectory 'compare.log')
}
Write-Output "SD_EXPLORER_RUN_RECORDED mode=$Mode results=$ResultsDirectory"
