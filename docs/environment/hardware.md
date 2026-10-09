# Confirmed hardware baseline — 2026-10-09

| Component | Specification |
|---|---|
| OS | Windows 10 |
| GPU | NVIDIA Tesla V100 |
| GPU VRAM | 32 GB |
| System RAM | 128 GB |
| Disk | 2 TB |
| Framework | ComfyUI |
| Repository | Public GitHub, including learning media with Git LFS |

User-provided hardware specifications are authoritative. Do not ask for the same details again. Driver version is unknown and should be checked only when needed for actual PyTorch compatibility or debugging. V100 uses Volta compute capability 7.0; avoid mandatory BF16, FlashAttention-2 and newer architecture-only kernels. Prior RTX 5090/Linux plan is superseded.
