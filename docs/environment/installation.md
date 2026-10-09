# Installation runbook (draft; unverified)

1. Run `bash scripts/check_gpu.sh` on the designated Linux host; record sanitized output in Phase 1 evidence.
2. Confirm supported Python, NVIDIA driver and PyTorch wheel compatibility for RTX 5090.
3. Clone upstream ComfyUI into an isolated workspace; pin tested commit and dependency versions after successful smoke test.
4. Download only approved commercially usable models; record upstream URLs, licenses, hashes and local storage paths (never weights).
5. Start ComfyUI bound to `127.0.0.1`; use SSH tunneling rather than exposing port 8188.
6. Run inference and export a short video; archive nonconfidential settings, timings and QC findings.

**Do not treat this draft as an executed installation.**
