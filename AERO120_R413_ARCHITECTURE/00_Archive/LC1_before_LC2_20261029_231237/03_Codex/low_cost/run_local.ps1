$ErrorActionPreference = 'Stop'
$env:AERO120_RUNTIME = 'C:\Users\nanwa\.codex\.chatgpt-projects\g-p-6ae08a8c33688191aa39a3e99fefcba6\.runtime'
$aeroPython = 'C:\Users\nanwa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
Push-Location $PSScriptRoot
try {
    & $aeroPython build.py
    if ($LASTEXITCODE -ne 0) { throw 'CAD build failed' }
    & $aeroPython -m unittest -v test_engineering
    if ($LASTEXITCODE -ne 0) { throw 'Engineering tests failed' }
} finally {
    Pop-Location
}
