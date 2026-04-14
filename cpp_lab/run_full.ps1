$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

$exeRelease = Join-Path $PSScriptRoot "build\Release\lab_benchmark.exe"
$exeDefault = Join-Path $PSScriptRoot "build\lab_benchmark.exe"

if (Test-Path $exeRelease) {
    $exe = $exeRelease
} elseif (Test-Path $exeDefault) {
    $exe = $exeDefault
} else {
    Write-Host "[error] lab_benchmark.exe not found. Run .\build.ps1 first."
    exit 1
}

& $exe --series 10 --cycles 20 --random-cycles 10 --search-ops 1000 --delete-ops 1000 --min-exponent 10 --output-dir outputs

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

python scripts/plot_results.py --input outputs/aggregated_results.csv --plots-dir outputs/plots
