param([string]$Root = "D:\AI-Video", [switch]$SafeMode)
$ErrorActionPreference = "Stop"
$python = Join-Path $Root ".venv\Scripts\python.exe"
$comfy = Join-Path $Root "ComfyUI"
if (-not (Test-Path $python)) { throw "Python environment not found: $python" }
if (-not (Test-Path (Join-Path $comfy "main.py"))) { throw "ComfyUI main.py missing: $comfy" }
Set-Location $comfy
if ($SafeMode) {
  Write-Host "Starting V100 compatibility mode: fp32, split attention, native CUDA allocator, no xformers, no custom nodes."
  $env:CUDA_LAUNCH_BLOCKING = "1"
  & $python main.py --listen 127.0.0.1 --port 8188 --disable-xformers --disable-all-custom-nodes --disable-cuda-malloc --use-split-cross-attention --force-fp32 --fp32-vae
} else {
  & $python main.py --listen 127.0.0.1 --port 8188 --disable-xformers
}
if ($LASTEXITCODE -ne 0) { throw "ComfyUI exited with code $LASTEXITCODE" }
