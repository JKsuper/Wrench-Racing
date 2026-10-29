param([string]$PythonExe = "")
$ErrorActionPreference = 'Stop'
if (-not $PythonExe) {
    $venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $venvPython) { $PythonExe = $venvPython }
    else { $PythonExe = 'python' }
}
Push-Location $PSScriptRoot
try {
    foreach ($script in @('build.py','views.py','appearance_views.py','profile_view.py')) {
        & $PythonExe -B $script
        if ($LASTEXITCODE -ne 0) { throw "Failed: $script" }
    }
    & $PythonExe -B -m unittest -v test_engineering
    if ($LASTEXITCODE -ne 0) { throw 'Geometry tests failed' }
    foreach ($script in @('print_preflight.py','prepare_print_shop.py','verify_handoff.py')) {
        & $PythonExe -B $script
        if ($LASTEXITCODE -ne 0) { throw "Failed: $script" }
    }
} finally { Pop-Location }
