$ErrorActionPreference='Stop'
$workspaceRoot=Split-Path -Parent $PSScriptRoot
Push-Location $workspaceRoot
try {
    $phaseLines=New-Object 'System.Collections.Generic.List[string]'
    foreach($startPhase in @(0,1,2,3,4)) {
        $phaseLines.Add("START_PHASE_NS=$startPhase")
        $phaseOutput=@(& powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test_qspi.ps1 -StartPhaseNs $startPhase 2>&1 | ForEach-Object { "$_" })
        $phaseExit=$LASTEXITCODE
        foreach($line in $phaseOutput){$phaseLines.Add($line);Write-Output $line}
        if($phaseExit -ne 0){throw "QSPI phase $startPhase failed"}
    }
    [IO.File]::WriteAllLines((Join-Path $workspaceRoot 'fpga/evidence/qspi-phase-sweep.log'),$phaseLines,(New-Object System.Text.UTF8Encoding($false)))
} finally {Pop-Location}
