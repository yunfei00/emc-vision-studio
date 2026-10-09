# Installation runbook — Windows 10 / Tesla V100 (draft, not executed)

1. In PowerShell run `powershell -ExecutionPolicy Bypass -File scripts/check_gpu.ps1` to record GPU VRAM, driver, OS, RAM, Python and Git.
2. Review PyTorch wheel, NVIDIA driver and Tesla V100 compute capability compatibility before installing. Do not assume latest wheels support sm_70.
3. Create a Python virtual environment or Conda environment and clone a pinned ComfyUI version.
4. Install a compatible PyTorch build, dependencies and model; record exact versions and model licenses.
5. Launch on `127.0.0.1:8188`, verify CUDA operations and render a short low-resolution test clip.
6. Commit scripts, sanitized logs, workflow, prompts, media and QA evidence. Use Git LFS for larger generated assets.

No installation or render has been performed yet. Use Windows PowerShell rather than Linux shell scripts.
