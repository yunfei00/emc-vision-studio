param([string]$Root = "D:\AI-Video")
$ErrorActionPreference = "Stop"
$python = Join-Path $Root ".venv\Scripts\python.exe"
$diagnostic = Join-Path $PSScriptRoot "diagnose_v100_inference.py"
if (-not (Test-Path $python)) { throw "Python executable not found: $python" }
if (-not (Test-Path $diagnostic)) { throw "Diagnostic file not found: $diagnostic" }
Write-Host "Running V100 diagnostics with Python file: $diagnostic"
& $python $diagnostic
if ($LASTEXITCODE -ne 0) { throw "Diagnostic Python process failed: $LASTEXITCODE" }
