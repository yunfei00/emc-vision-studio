param([string]$Root = "D:\AI-Video")
$ErrorActionPreference = "Stop"
$python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Python not found: $python" }
& $python (Join-Path $PSScriptRoot "make_phase7_story_cut.py") --root $Root
if ($LASTEXITCODE -ne 0) { throw "Phase 7 failed with code $LASTEXITCODE" }
