param([string]$Root = "D:\AI-Video")
$ErrorActionPreference = "Stop"
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw "未找到 uv，请先按 docs/operations/2026-10-09-phase1-windows-v100.md 安装 uv。" }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "未找到 Git，请先安装 Git for Windows。" }
New-Item -ItemType Directory -Force -Path $Root | Out-Null
$comfy = Join-Path $Root "ComfyUI"
$venv = Join-Path $Root ".venv"
if (-not (Test-Path (Join-Path $comfy ".git"))) {
  git clone https://github.com/Comfy-Org/ComfyUI.git $comfy
  if ($LASTEXITCODE -ne 0) { throw "ComfyUI 克隆失败" }
}
uv python install 3.12
if ($LASTEXITCODE -ne 0) { throw "uv 安装 Python 3.12 失败" }
if (-not (Test-Path (Join-Path $venv "Scripts\python.exe"))) {
  uv venv $venv --python 3.12
  if ($LASTEXITCODE -ne 0) { throw "uv 创建虚拟环境失败" }
}
$python = Join-Path $venv "Scripts\python.exe"
uv pip install --python $python torch==2.7.0 torchvision==0.22.0 torchaudio==2.7.0 --index-url https://download.pytorch.org/whl/cu126
if ($LASTEXITCODE -ne 0) { throw "PyTorch 安装失败" }
& $python -c "import torch; print('torch',torch.__version__,'cuda',torch.version.cuda); assert torch.cuda.is_available(); print('GPU',torch.cuda.get_device_name(0)); print('arches',torch.cuda.get_arch_list()); assert 'sm_70' in torch.cuda.get_arch_list(), '当前 PyTorch 未包含 V100 sm_70'; x=torch.ones((32,32),device='cuda'); assert float((x@x)[0,0])==32"
if ($LASTEXITCODE -ne 0) { throw "V100 GPU 实算测试失败；请停止并记录报错" }
uv pip install --python $python -r (Join-Path $comfy "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "ComfyUI 依赖安装失败" }
& $python -c "import torch; print('GPU',torch.cuda.get_device_name(0)); assert torch.cuda.is_available(); assert 'sm_70' in torch.cuda.get_arch_list(); x=torch.ones((32,32),device='cuda'); assert float((x@x)[0,0])==32"
if ($LASTEXITCODE -ne 0) { throw "依赖安装后 GPU 验证失败，不能验收" }
Write-Host "uv 环境安装完成；视频模型及真实渲染尚未完成。启动脚本：scripts/start_windows_v100.ps1"
