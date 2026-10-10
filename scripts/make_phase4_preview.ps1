param([string]$Root = "D:\AI-Video")
$ErrorActionPreference = "Stop"
$python = Join-Path $Root ".venv\Scripts\python.exe"
$script = Join-Path $PSScriptRoot "make_phase4_preview.py"
if (-not (Test-Path $python)) { throw "Python not found: $python" }
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { throw "FFmpeg not found. See docs/operations/2026-10-10-phase4-video-preview.md" }
& $python $script --root $Root
if ($LASTEXITCODE -ne 0) { throw "Phase 4 preview failed with code $LASTEXITCODE" }
