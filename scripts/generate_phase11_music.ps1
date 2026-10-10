param([string]$Root = "D:\AI-Video")
$ErrorActionPreference = "Stop"
$python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Python not found: $python" }
& $python (Join-Path $PSScriptRoot "generate_phase11_music.py") --root $Root
if ($LASTEXITCODE -ne 0) { throw "Music generation failed: $LASTEXITCODE" }
& $python (Join-Path $PSScriptRoot "make_phase11_delivery.py") --root $Root
if ($LASTEXITCODE -ne 0) { throw "Delivery refresh failed: $LASTEXITCODE" }
