import argparse
import json
import pathlib
import subprocess
import sys
import time
import urllib.request

def request_json(url, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as res:
        return json.load(res)

def wait(server, prompt_id, timeout):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        history = request_json(server + "/history/" + prompt_id).get(prompt_id)
        if history:
            status = history.get("status", {})
            for msg in status.get("messages", []):
                if isinstance(msg, list) and len(msg) == 2 and msg[0] == "execution_error":
                    info = msg[1]
                    raise RuntimeError("FAILED NODE: {} {}\nEXCEPTION: {}\nTRACEBACK:\n{}".format(info.get("node_id"), info.get("node_type"), info.get("exception_message"), "".join(info.get("traceback", []))))
            if status.get("completed"):
                return history.get("outputs", {})
            if status.get("status_str") == "error":
                raise RuntimeError(json.dumps(status, ensure_ascii=False))
        time.sleep(3)
    raise TimeoutError("SVD prompt timed out after {} seconds".format(timeout))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="D:/AI-Video")
    p.add_argument("--server", default="http://127.0.0.1:8188")
    p.add_argument("--timeout", type=int, default=2400)
    args = p.parse_args()
    root = pathlib.Path(args.root)
    images = sorted((root / "ComfyUI" / "output").glob("lost_signal_phase3_S001_*.png"))
    if not images:
        raise FileNotFoundError("S001 image not found")
    model = root / "ComfyUI" / "models" / "checkpoints" / "svd.safetensors"
    if not model.is_file():
        raise FileNotFoundError(str(model))
    local = root / "private" / "lost-signal" / "phase5"
    local.mkdir(parents=True, exist_ok=True)
    image = images[-1]
    # ComfyUI LoadImage reads from its input directory, so copy locally.
    import shutil
    name = "lost_signal_phase5_S001_input.png"
    shutil.copy2(image, root / "ComfyUI" / "input" / name)
    server = args.server.rstrip("/")
    nodes = request_json(server + "/object_info")
    required = ["ImageOnlyCheckpointLoader", "SVD_img2vid_Conditioning", "VideoLinearCFGGuidance", "KSampler", "VAEDecode", "SaveImage", "LoadImage"]
    missing = [node for node in required if node not in nodes]
    if missing:
        raise RuntimeError("Missing ComfyUI nodes: " + ", ".join(missing))
    workflow = {
      "1": {"class_type": "ImageOnlyCheckpointLoader", "inputs": {"ckpt_name": "svd.safetensors"}},
      "2": {"class_type": "LoadImage", "inputs": {"image": name}},
      "3": {"class_type": "SVD_img2vid_Conditioning", "inputs": {"width": 1024, "height": 576, "video_frames": 14, "motion_bucket_id": 127, "fps": 6, "augmentation_level": 0, "clip_vision": ["1", 1], "init_image": ["2", 0], "vae": ["1", 2]}},
      "4": {"class_type": "VideoLinearCFGGuidance", "inputs": {"model": ["1", 0], "min_cfg": 1}},
      "5": {"class_type": "KSampler", "inputs": {"seed": 20261010, "steps": 20, "cfg": 2.5, "sampler_name": "euler", "scheduler": "karras", "denoise": 1, "model": ["4", 0], "positive": ["3", 0], "negative": ["3", 1], "latent_image": ["3", 2]}},
      "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
      "7": {"class_type": "SaveImage", "inputs": {"filename_prefix": "lost_signal_phase5_S001", "images": ["6", 0]}}
    }
    # Check required input names against the live node schema before queuing.
    for node in workflow.values():
        definition = nodes[node["class_type"]].get("input", {})
        accepted = set(definition.get("required", {})) | set(definition.get("optional", {}))
        invalid = set(node["inputs"]) - accepted
        if invalid:
            raise RuntimeError("Unsupported inputs for {}: {}".format(node["class_type"], sorted(invalid)))
    print("SVD 14-FRAME INFERENCE STARTING. All media stays local.", flush=True)
    result = request_json(server + "/prompt", {"prompt": workflow, "client_id": "emc-vision-studio-phase5"})
    if "prompt_id" not in result:
        raise RuntimeError("ComfyUI rejected workflow: " + json.dumps(result, ensure_ascii=False))
    outputs = wait(server, result["prompt_id"], args.timeout)
    names = [img["filename"] for output in outputs.values() for img in output.get("images", [])]
    if len(names) != 14:
        raise RuntimeError("Expected 14 frames, received {}: {}".format(len(names), names))
    frames = []
    for name in names:
        source = root / "ComfyUI" / "output" / name
        if not source.is_file():
            raise FileNotFoundError(str(source))
        frames.append(source)
    for idx, source in enumerate(frames):
        shutil.copy2(source, local / ("frame_%03d.png" % idx))
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("14 frames generated, but FFmpeg is not in PATH")
    output = local / "S001_svd_14frames.mp4"
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-framerate", "6", "-i", str(local / "frame_%03d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", str(output)]
    subprocess.run(cmd, check=True)
    (local / "manifest.json").write_text(json.dumps({"status": "complete", "prompt_id": result["prompt_id"], "frame_count": 14, "fps": 6, "output": str(output)}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("SVD SUCCESS: 14 frames", flush=True)
    print("LOCAL MP4:", output, flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("SVD FAILED:", exc, file=sys.stderr, flush=True)
        sys.exit(1)
