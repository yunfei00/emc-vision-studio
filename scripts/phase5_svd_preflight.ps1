param([string]$Root = "D:\AI-Video")
$ErrorActionPreference = "Stop"
$python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Python not found: $python" }
& $python (Join-Path $PSScriptRoot "phase5_svd_preflight.py") $Root
if ($LASTEXITCODE -ne 0) { throw "Phase 5 preflight failed" }
