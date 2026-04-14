param(
    [string]$BuildType = "Release"
)

$ErrorActionPreference = "Stop"

Write-Host "[info] Working in cpp_lab"
Set-Location $PSScriptRoot

function Get-CMakePath {
    $cmakeInPath = Get-Command cmake -ErrorAction SilentlyContinue
    if ($cmakeInPath) {
        return "cmake"
    }

    $vsCmake = "C:\Program Files\Microsoft Visual Studio\18\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"
    if (Test-Path $vsCmake) {
        return $vsCmake
    }

    return $null
}

$cmakePath = Get-CMakePath
if (-not $cmakePath) {
    Write-Host "[error] CMake not found in PATH and Visual Studio bundled CMake was not found."
    exit 1
}

$vsDev = "C:\Program Files\Microsoft Visual Studio\18\Community\Common7\Tools\VsDevCmd.bat"
if (-not (Test-Path $vsDev)) {
    Write-Host "[error] VsDevCmd.bat not found. Install Visual Studio C++ workload."
    exit 1
}

$cmakeQuoted = '"' + $cmakePath + '"'
$proj = '"' + $PSScriptRoot + '"'
$cmd = '"' + $vsDev + '" -arch=x64 -host_arch=x64 >nul && ' +
       $cmakeQuoted + ' -S ' + $proj + ' -B ' + $proj + '\build -DCMAKE_BUILD_TYPE=' + $BuildType + ' && ' +
       $cmakeQuoted + ' --build ' + $proj + '\build --config ' + $BuildType

cmd /c $cmd
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "[ok] Build complete."
