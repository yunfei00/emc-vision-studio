param([string]$Root = "D:\AI-Video")
$ErrorActionPreference = "Stop"
$python = Join-Path $Root ".venv\Scripts\python.exe"
$comfy = Join-Path $Root "ComfyUI"
if (-not (Test-Path $python)) { throw "找不到 Python 环境：$python；请修改 -Root 为实际安装目录。" }
if (-not (Test-Path (Join-Path $comfy "main.py"))) { throw "找不到 ComfyUI：$comfy" }
Write-Host "===== 第一步：V100 CUDA 实际计算 ====="
& $python -c "import torch; print('PyTorch:',torch.__version__); print('CUDA:',torch.version.cuda); print('GPU:',torch.cuda.get_device_name(0) if torch.cuda.is_available() else '不可用'); assert torch.cuda.is_available(), 'CUDA 不可用'; print('架构:',torch.cuda.get_device_capability(0)); a=torch.ones((256,256),device='cuda'); b=a@a; torch.cuda.synchronize(); assert float(b[0,0])==256; print('CUDA 矩阵运算：通过')"
if ($LASTEXITCODE -ne 0) { throw "CUDA 验证失败，已停止后续步骤。" }
Write-Host "===== 第二步：检查 ComfyUI 模型目录 ====="
$models = Join-Path $comfy "models"
$checkpoint = Join-Path $models "checkpoints"
New-Item -ItemType Directory -Force -Path $checkpoint | Out-Null
Write-Host "模型目录：$checkpoint"
Write-Host "===== 第三步：查看已有模型 ====="
Get-ChildItem -Path $checkpoint -File -ErrorAction SilentlyContinue | Select-Object Name,Length | Format-Table -AutoSize
Write-Host "验证完成。尚未下载或安装任何图像/视频模型。"
