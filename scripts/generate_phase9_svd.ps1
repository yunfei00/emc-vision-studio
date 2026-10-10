param([string]$Root = "D:\AI-Video")
$ErrorActionPreference = "Stop"
$python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Python not found: $python" }
& $python (Join-Path $PSScriptRoot "generate_phase9_svd.py") --root $Root
if ($LASTEXITCODE -ne 0) { throw "Phase 9 AI clip generation failed: $LASTEXITCODE" }
