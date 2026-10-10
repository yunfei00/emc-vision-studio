param([string]$Root = "D:\AI-Video")
$ErrorActionPreference = "Stop"
$python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Python executable not found: $python" }
$code = @'
import sys, traceback
import torch
print("Python:", sys.version.split()[0])
print("PyTorch:", torch.__version__, "CUDA runtime:", torch.version.cuda)
print("GPU available:", torch.cuda.is_available())
if not torch.cuda.is_available():
    raise RuntimeError("CUDA unavailable")
print("GPU:", torch.cuda.get_device_name(0), "capability:", torch.cuda.get_device_capability(0))
print("Supported architectures:", torch.cuda.get_arch_list())
def test(name, fn):
    try:
        fn()
        torch.cuda.synchronize()
        print("PASS:", name)
    except Exception:
        print("FAIL:", name)
        traceback.print_exc()
def matmul():
    x = torch.ones((256,256), device="cuda", dtype=torch.float32)
    y = x @ x
    assert float(y[0,0]) == 256
def conv():
    layer = torch.nn.Conv2d(4, 8, 3, padding=1).cuda().float()
    x = torch.randn((1,4,64,64), device="cuda", dtype=torch.float32)
    assert layer(x).shape == (1,8,64,64)
def attention():
    q = torch.randn((1,4,128,64), device="cuda", dtype=torch.float32)
    with torch.backends.cuda.sdp_kernel(enable_flash=False, enable_math=True, enable_mem_efficient=False):
        torch.nn.functional.scaled_dot_product_attention(q,q,q)
test("fp32 matmul", matmul)
test("fp32 convolution", conv)
test("math SDPA", attention)
'@
& $python -c $code
if ($LASTEXITCODE -ne 0) { throw "Diagnostic Python process failed: $LASTEXITCODE" }
