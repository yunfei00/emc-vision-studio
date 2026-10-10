param([string]$Root = "D:\AI-Video")
$ErrorActionPreference = "Stop"
$python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Python not found: $python" }
& $python (Join-Path $PSScriptRoot "generate_phase6_svd_all.py") --root $Root
if ($LASTEXITCODE -ne 0) { throw "Phase 6 SVD batch failed: $LASTEXITCODE" }
