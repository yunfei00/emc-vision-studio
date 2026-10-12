"""P4.2: verify local inputs, ComfyUI API and V100 readiness without generating media."""
import argparse
import json
import shutil
import subprocess
import urllib.request
from pathlib import Path

SHOTS = {"S007": "003_S007_010s.png", "S010": "008_S010_036s.png", "S016": "015_S016_075s.png"}
REQUIRED = ("ImageOnlyCheckpointLoader", "LoadImage", "SVD_img2vid_Conditioning", "VideoLinearCFGGuidance", "KSampler", "VAEDecode", "SaveImage")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="D:/AI-Video")
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    args = ap.parse_args()
    root = Path(args.root)
    base = root / "private/lost-signal/v0.2"
    issues, info = [], {"scenes": {}}
    for sid, filename in SHOTS.items():
        p = base / "keyframes" / filename
        info["scenes"][sid] = {"file": str(p), "exists": p.is_file()}
        if not p.is_file(): issues.append(f"{sid}: missing {filename}")
    model = root / "ComfyUI/models/checkpoints/svd.safetensors"
    info["svd_model"] = str(model)
    if not model.is_file(): issues.append("SVD checkpoint not found at expected location")
    for name in ("ffmpeg", "ffprobe"):
        info[name] = shutil.which(name)
        if not info[name]: issues.append(name + " not found on PATH")
    gpu = shutil.which("nvidia-smi")
    if gpu:
        p = subprocess.run([gpu, "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader"], capture_output=True, text=True)
        info["gpu"] = p.stdout.strip() if p.returncode == 0 else p.stderr.strip()[:500]
    else:
        issues.append("nvidia-smi not on PATH")
    try:
        with urllib.request.urlopen(args.server.rstrip("/") + "/object_info", timeout=12) as r:
            nodes = json.load(r)
        info["comfyui_api"] = "online"
        missing = [name for name in REQUIRED if name not in nodes]
        if missing: issues.append("ComfyUI missing nodes: " + ", ".join(missing))
    except Exception as exc:
        info["comfyui_api"] = str(exc)
        issues.append("ComfyUI API unavailable (start SafeMode first)")
    info["issues"] = issues
    info["status"] = "READY" if not issues else "NOT_READY"
    dest = base / "p4/reports/video_preflight.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    print("P4.2", info["status"])
    print("GPU:", info.get("gpu", "unknown"))
    print("ComfyUI:", info.get("comfyui_api"))
    for issue in issues: print("CHECK:", issue)
    print("Report:", dest)
    return 0 if not issues else 2

if __name__ == "__main__":
    raise SystemExit(main())
