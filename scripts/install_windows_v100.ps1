param([string]$Root = "D:\\AI-Video")
$ErrorActionPreference = "Stop"
Write-Host "Installing ComfyUI for Tesla V100 in $Root"
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Git is required: https://git-scm.com/download/win" }
if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw "Python 3.12 x64 launcher required: https://www.python.org/downloads/windows/" }
$ver = & py -3.12 -c "import struct; print(struct.calcsize('P') * 8)"
if ($LASTEXITCODE -ne 0 -or $ver.Trim() -ne "64") { throw "Install 64-bit Python 3.12 first" }
New-Item -ItemType Directory -Force -Path $Root | Out-Null
$comfy = Join-Path $Root "ComfyUI"
if (-not (Test-Path (Join-Path $comfy ".git"))) { git clone https://github.com/Comfy-Org/ComfyUI.git $comfy; if ($LASTEXITCODE -ne 0) { throw "Git clone failed" } }
$venv = Join-Path $Root ".venv"
if (-not (Test-Path (Join-Path $venv "Scripts\python.exe"))) { & py -3.12 -m venv $venv }
$python = Join-Path $venv "Scripts\python.exe"
& $python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed" }
& $python -m pip install torch==2.7.0 torchvision==0.22.0 torchaudio==2.7.0 --index-url https://download.pytorch.org/whl/cu126
if ($LASTEXITCODE -ne 0) { throw "PyTorch installation failed" }
& $python -c "import torch; print(torch.__version__,torch.version.cuda,torch.cuda.get_device_name(0)); assert torch.cuda.is_available(); assert (7,0) in torch.cuda.get_arch_list() or 'sm_70' in torch.cuda.get_arch_list(); x=torch.ones((32,32),device='cuda'); assert float((x@x)[0,0])==32"
if ($LASTEXITCODE -ne 0) { throw "GPU smoke test failed; do not proceed. See docs/operations/2026-10-09-phase1-windows-v100.md" }
& $python -m pip install -r (Join-Path $comfy "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "ComfyUI dependencies failed; inspect dependency conflicts" }
Write-Host "Installed. Start using scripts/start_windows_v100.ps1. No video model has been installed."
