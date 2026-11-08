[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Output,
    [switch]$Apply,
    [string]$Plan
)
$ErrorActionPreference='Stop'
$target='USB\VID_1209&PID_B010\802C0E7A'
$expectedRevision='USB\VID_1209&PID_B010&REV_0411'
$helper=Join-Path $PSScriptRoot 'BindGameBubWinUsb.exe'
$source=Join-Path $PSScriptRoot 'BindGameBubWinUsb.cs'
$inboxInf=Join-Path $env:windir 'INF\winusb.inf'
$inboxSys=Join-Path $env:windir 'System32\drivers\WinUSB.sys'
$resolvedOutput=[IO.Path]::GetFullPath($Output)
if(-not $resolvedOutput.StartsWith('C:\moon\',[StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $resolvedOutput)){throw 'Use a new unique output directory below C:/moon'}
if(-not [Environment]::Is64BitProcess){throw 'Run 64-bit PowerShell'}
foreach($p in @($helper,$source,$inboxInf,$inboxSys)) {if(-not(Test-Path -LiteralPath $p -PathType Leaf)){throw "Required exact file absent: $p"}}
$signature=Get-AuthenticodeSignature -LiteralPath $inboxSys
if($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Microsoft'){throw 'In-box WinUSB.sys signature was not validated as Microsoft'}
$before=Get-PnpDevice -PresentOnly | Where-Object {$_.InstanceId -ceq $target}
if(@($before).Count -ne 1){throw 'Exactly one present target updater is required'}
$hardware=(Get-PnpDeviceProperty -InstanceId $target -KeyName DEVPKEY_Device_HardwareIds).Data
$problem=(Get-PnpDeviceProperty -InstanceId $target -KeyName DEVPKEY_Device_ProblemCode).Data
if($hardware -notcontains $expectedRevision -or $problem -ne 28){throw 'Target must be exact unbound REV0411 updater/code28'}
if($Apply){
    if(-not $Plan){throw '-Apply requires the reviewed read-only preflight.json'}
    if(-not([Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))){throw 'An already elevated administrator token is required; this script never self-elevates'}
}
$evidence=[ordered]@{
    schema='moonbub-inbox-winusb-system-v1';utc=[DateTime]::UtcNow.ToString('o');target=$target;expected_revision=$expectedRevision
    apply_requested=[bool]$Apply;helper_sha256=(Get-FileHash -LiteralPath $helper -Algorithm SHA256).Hash.ToLowerInvariant()
    helper_source_sha256=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
    wrapper_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
    inbox_inf_sha256=(Get-FileHash -LiteralPath $inboxInf -Algorithm SHA256).Hash.ToLowerInvariant()
    inbox_sys_sha256=(Get-FileHash -LiteralPath $inboxSys -Algorithm SHA256).Hash.ToLowerInvariant()
    sys_authenticode_status=$signature.Status.ToString();sys_signer=$signature.SignerCertificate.Subject
    before=$before;hardware_ids=$hardware;problem_code=$problem;no_driver_downloads=$true;no_unsigned_inf=$true;no_flash_operations=$true
}
$arguments=@('--output',$resolvedOutput,'--expected-instance',$target)
if($Apply){$arguments+=@('--apply','--plan',[IO.Path]::GetFullPath($Plan))}
try { & $helper @arguments; $helperExit=$LASTEXITCODE }
finally {
    if(Test-Path -LiteralPath $resolvedOutput -PathType Container){
        $evidencePath=Join-Path $resolvedOutput 'system-evidence.json'
        $text=$evidence|ConvertTo-Json -Depth 8
        $bytes=[Text.Encoding]::UTF8.GetBytes($text+[Environment]::NewLine)
        $stream=[IO.File]::Open($evidencePath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
        try{$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
    }
}
if($helperExit -ne 0){throw "Scoped helper stopped with exit $helperExit; inspect preserved output. No automatic retry or reboot."}
Write-Output "Scoped result preserved at $resolvedOutput"
