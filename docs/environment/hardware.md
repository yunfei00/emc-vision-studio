# Hardware baseline — 2026-10-09

**Confirmed by user:** Windows 10 workstation, NVIDIA Tesla V100, 128 GB system RAM. GPU VRAM capacity, driver and CUDA runtime are pending inspection. The previous RTX 5090/Linux plan is superseded for this project.

Tesla V100 is Volta (compute capability 7.0). Do not assume BF16, FlashAttention-2 or recent CUDA-only attention kernels work. Prefer validated FP16 and conservative offloading; model support and commercial license must be checked before download.

Run `powershell -ExecutionPolicy Bypass -File scripts/check_gpu.ps1` and attach results to Phase 1 acceptance.
