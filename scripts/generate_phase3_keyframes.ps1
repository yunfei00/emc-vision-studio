param([string]$Root = "D:\AI-Video", [string]$Server = "http://127.0.0.1:8188")
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$python = Join-Path $Root ".venv\Scripts\python.exe"
$script = Join-Path $PSScriptRoot "generate_phase3_keyframes.py"
if (-not (Test-Path $python)) { throw "Python not found: $python" }
& $python $script --root $Root --repo $repo --server $Server
if ($LASTEXITCODE -ne 0) { throw "Phase 3 keyframe generation failed: $LASTEXITCODE" }
