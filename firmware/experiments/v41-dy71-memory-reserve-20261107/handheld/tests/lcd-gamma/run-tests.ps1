param([ValidateSet('all', 'rev2', 'rev3', 'rev4')][string]$Board = 'all')
$ErrorActionPreference = 'Stop'
$repository = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$cargo = Join-Path $env:USERPROFILE '.cargo/bin/cargo.exe'
$boards = if ($Board -eq 'all') { @('rev2', 'rev3', 'rev4') } else { @($Board) }
Push-Location $repository
try {
    foreach ($revision in $boards) {
        Write-Output "Testing LCD gamma: $revision"
        $ErrorActionPreference = 'Continue'
        & $cargo +stable test --locked --manifest-path firmware/handheld/tests/lcd-gamma/Cargo.toml `
            --target x86_64-pc-windows-msvc --no-default-features --features $revision 2>&1 |
            ForEach-Object { "$_" }
        $ErrorActionPreference = 'Stop'
        if ($LASTEXITCODE -ne 0) { throw "LCD gamma tests failed: $revision" }
    }
} finally {
    Pop-Location
}
