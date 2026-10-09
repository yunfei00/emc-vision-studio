param([string]$Root = "D:\AI-Video")
$ErrorActionPreference = "Stop"
$python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "找不到 uv 环境：$python。请核对 -Root 路径。" }
Write-Host "=== Tesla V100 CUDA 验证 ==="
& $python -c "import torch; print('PyTorch:',torch.__version__); print('CUDA:',torch.version.cuda); print('GPU 可用:',torch.cuda.is_available()); assert torch.cuda.is_available(), 'CUDA 不可用'; print('GPU:',torch.cuda.get_device_name(0)); print('GPU 架构:',torch.cuda.get_device_capability(0)); print('支持架构:',torch.cuda.get_arch_list()); assert torch.cuda.get_device_capability(0)==(7,0), '不是 Tesla V100 sm_70'; x=torch.randn((512,512),device='cuda'); y=x@x; torch.cuda.synchronize(); assert torch.isfinite(y).all().item(); print('CUDA 矩阵运算：通过')"
if ($LASTEXITCODE -ne 0) { throw "CUDA 验证失败，不能进入模型生成阶段。" }
Write-Host "CUDA 基础验证通过。注意：尚未验证实际 AI 视频模型。"
