#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
import torch
print('torch', torch.__version__, 'CUDA build', torch.version.cuda)
assert torch.cuda.is_available(), 'CUDA GPU unavailable'
print('GPU', torch.cuda.get_device_name(0))
x=torch.randn((128,128),device='cuda'); y=x@x
assert torch.isfinite(y).all().item()
print('CUDA smoke test PASS')
PY
