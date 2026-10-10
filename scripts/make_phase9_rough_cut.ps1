param([string]$Root = "D:\AI-Video")
$ErrorActionPreference = "Stop"
$python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Python not found: $python" }
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
& $python (Join-Path $PSScriptRoot "make_phase9_rough_cut.py") --root $Root --repo $repo
if ($LASTEXITCODE -ne 0) { throw "Phase 9 rough cut failed: $LASTEXITCODE" }
