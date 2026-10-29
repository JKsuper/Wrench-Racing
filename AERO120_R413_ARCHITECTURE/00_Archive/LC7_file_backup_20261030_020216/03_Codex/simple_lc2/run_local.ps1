$ErrorActionPreference = 'Stop'
$env:AERO120_RUNTIME = 'C:\Users\nanwa\.codex\.chatgpt-projects\g-p-6ae08a8c33688191aa39a3e99fefcba6\.runtime'
$aeroPython = 'C:\Users\nanwa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
Push-Location $PSScriptRoot
try {
    & $aeroPython -B build.py --hand R
    if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
    & $aeroPython -B views.py
    if ($LASTEXITCODE -ne 0) { throw 'Section rendering failed' }
    & $aeroPython -B appearance_views.py
    if ($LASTEXITCODE -ne 0) { throw 'Appearance render failed' }
    & $aeroPython -B -m unittest -v test_engineering
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
} finally { Pop-Location }
