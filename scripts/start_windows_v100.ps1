param([string]$Root = "D:\\AI-Video")
$python = Join-Path $Root ".venv\Scripts\python.exe"
$comfy = Join-Path $Root "ComfyUI"
if (-not (Test-Path $python)) { throw "Run install_windows_v100.ps1 first" }
if (-not (Test-Path (Join-Path $comfy "main.py"))) { throw "ComfyUI missing" }
Set-Location $comfy
& $python main.py --listen 127.0.0.1 --port 8188 --disable-xformers
