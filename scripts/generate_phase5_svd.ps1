param([string]$Root = "D:\AI-Video")
$ErrorActionPreference = "Stop"
$python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Python not found: $python" }
& $python (Join-Path $PSScriptRoot "generate_phase5_svd.py") --root $Root
if ($LASTEXITCODE -ne 0) { throw "Phase 5 SVD inference failed: $LASTEXITCODE" }
