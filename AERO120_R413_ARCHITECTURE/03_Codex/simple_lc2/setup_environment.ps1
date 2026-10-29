param([string]$PythonExe = "python")
$ErrorActionPreference = 'Stop'
$venv = Join-Path $PSScriptRoot '.venv'
& $PythonExe -m venv $venv
if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 x64 is recommended; environment creation failed' }
$localPython = Join-Path $venv 'Scripts\python.exe'
& $localPython -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
& $localPython -c "import cadquery, vtk, matplotlib; print(cadquery.__version__)"
if ($LASTEXITCODE -ne 0) { throw 'Dependency import failed' }
