param([string]$Root = "D:\AI-Video")
$ErrorActionPreference = "Stop"
$python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Python not found: $python" }
& $python (Join-Path $PSScriptRoot "v02_p1_quality_baseline.py") --root $Root
if ($LASTEXITCODE -ne 0) { throw "v0.2 P1 failed: $LASTEXITCODE" }
