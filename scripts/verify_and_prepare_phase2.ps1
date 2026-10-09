param([string]$Root = "D:\AI-Video")
$ErrorActionPreference = "Stop"
$python = Join-Path $Root ".venv\Scripts\python.exe"
$comfy = Join-Path $Root "ComfyUI"
if (-not (Test-Path $python)) { throw "Python executable not found: $python. Check -Root." }
if (-not (Test-Path (Join-Path $comfy "main.py"))) { throw "ComfyUI main.py not found: $comfy" }
Write-Host "STEP 1: CUDA compute verification"
$code = "import torch; print('PyTorch:',torch.__version__); print('CUDA:',torch.version.cuda); print('GPU:',torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'unavailable'); assert torch.cuda.is_available(), 'CUDA unavailable'; print('Capability:',torch.cuda.get_device_capability(0)); a=torch.ones((256,256),device='cuda'); b=a@a; torch.cuda.synchronize(); assert float(b[0,0])==256; print('CUDA COMPUTE PASS')"
& $python -c $code
if ($LASTEXITCODE -ne 0) { throw "CUDA verification failed. Stop here and inspect the error above." }
Write-Host "STEP 2: Check ComfyUI model directory"
$checkpoint = Join-Path (Join-Path $comfy "models") "checkpoints"
New-Item -ItemType Directory -Force -Path $checkpoint | Out-Null
Write-Host "MODEL DIRECTORY: $checkpoint"
Write-Host "STEP 3: Existing model files"
Get-ChildItem -Path $checkpoint -File -ErrorAction SilentlyContinue | Select-Object Name,Length | Format-Table -AutoSize
Write-Host "VERIFICATION COMPLETE"
