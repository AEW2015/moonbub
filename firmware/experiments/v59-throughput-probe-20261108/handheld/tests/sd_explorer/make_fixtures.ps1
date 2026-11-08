param([string]$OutputDirectory = (Join-Path $PSScriptRoot 'staging'),[string]$RunId='sd-explorer-default')
$ErrorActionPreference='Stop'
$root=Join-Path (Resolve-Path $OutputDirectory) "GBTEST/$RunId"
if(Test-Path -LiteralPath $root){throw "Refusing existing suite directory: $root"}
New-Item -ItemType Directory -Path $root,(Join-Path $root 'empty'),(Join-Path $root 'deep/a/b/c/d/e/f'),(Join-Path $root 'many') -Force|Out-Null
$seed=[Text.Encoding]::ASCII.GetBytes('GameBub SD Explorer deterministic fixture v1')
function Write-Fixture([string]$Relative,[int]$Length){$p=Join-Path $root $Relative;$d=Split-Path $p -Parent;New-Item -ItemType Directory -Path $d -Force|Out-Null;$b=New-Object byte[] $Length;for($i=0;$i -lt $Length;$i++){$b[$i]=$seed[$i%$seed.Length] -bxor ($i-band 255)};[IO.File]::WriteAllBytes($p,$b)}
foreach($n in 0,1,255,256,511,512,513,4095,4096,4097,65537){Write-Fixture "boundaries/$n.bin" $n}
Write-Fixture 'assets/demo image.png' 513;Write-Fixture 'assets/sound.WAV' 512;Write-Fixture 'assets/model.obj' 4097;Write-Fixture 'assets/multi.part.name.txt' 255;Write-Fixture 'deep/a/b/c/d/e/f/final.json' 256
for($i=0;$i -lt 257;$i++){Write-Fixture ("many/item-{0:d3}.dat" -f $i) (($i%17)+1)}
[IO.File]::WriteAllText((Join-Path $root '.GBTEST-SENTINEL'),"suite=gamebub-sd-explorer-v1`nrun=$RunId`n",[Text.Encoding]::UTF8)
$manifest=Get-ChildItem $root -Recurse -Force|ForEach-Object {if($_.PSIsContainer){[pscustomobject]@{path=$_.FullName.Substring($root.Length+1).Replace('\','/');kind='dir';bytes=0;sha256=$null}}else{[pscustomobject]@{path=$_.FullName.Substring($root.Length+1).Replace('\','/');kind='file';bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower()}}}
$manifest|ConvertTo-Json -Depth 3|Set-Content (Join-Path (Split-Path $root -Parent) 'manifest.json') -Encoding utf8
Write-Output "SD_EXPLORER_FIXTURES_PASS root=$root entries=$($manifest.Count)"
