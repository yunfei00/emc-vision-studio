import json
import pathlib
import sys
import urllib.request

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "D:/AI-Video")
out = root / "private" / "lost-signal" / "phase5"
out.mkdir(parents=True, exist_ok=True)
images = sorted((root / "ComfyUI" / "output").glob("lost_signal_phase3_S001_*.png"))
models = sorted((root / "ComfyUI" / "models" / "checkpoints").glob("svd*.safetensors"))
report = {"source_exists": bool(images), "source": str(images[-1]) if images else None,
          "svd_model_found": [p.name for p in models],
          "api_reachable": False, "required_nodes": {}, "ready": False}
try:
    with urllib.request.urlopen("http://127.0.0.1:8188/object_info", timeout=10) as r:
        nodes = json.load(r)
    report["api_reachable"] = True
    for name in ("ImageOnlyCheckpointLoader", "SVD_img2vid_Conditioning", "VideoLinearCFGGuidance", "KSampler", "VAEDecode", "SaveImage", "LoadImage"):
        report["required_nodes"][name] = name in nodes
except Exception as e:
    report["api_error"] = str(e)
report["ready"] = report["source_exists"] and report["api_reachable"] and all(report["required_nodes"].values()) and bool(report["svd_model_found"])
(out / "preflight.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print("S001 IMAGE:", "PASS" if report["source_exists"] else "MISSING")
print("COMFY API:", "PASS" if report["api_reachable"] else "UNAVAILABLE")
print("SVD NODES:", report["required_nodes"])
print("SVD MODEL:", report["svd_model_found"] if models else "NOT INSTALLED")
print("READY FOR SVD:", report["ready"])
print("LOCAL REPORT:", out / "preflight.json")
