# EMC Vision Studio

Local AI video production and technical storytelling project for smartphone EMC/GNSS interference. First film: 《消失的信号》 (90–120s main film plus 30s cutdown).

## Primary workstation
Windows 10, Tesla V100, 128 GB system RAM. GPU VRAM and driver are pending inspection. The earlier RTX 5090/Linux assumptions are superseded. Start with `scripts/check_gpu.ps1` and `docs/environment/installation.md`.

## Workflow
Phase 0 project baseline; Phase 1 ComfyUI environment and test render; Phase 2 technical script/storyboard; Phase 3 shot generation; Phase 4 editing/audio; Phase 5 company release review. See `docs/roadmap.md` and `docs/progress.md`.

## GitHub asset policy
Public repository includes study documents, workflows, prompts, test images, generated clips, audio and approved deliverables. Use Git LFS for large media; keep model weights, caches and secrets out of Git. Public visibility means content is accessible to everyone; confirm permission for any company or third-party material. Synthetic instrument readings must not be represented as real measurement evidence.
