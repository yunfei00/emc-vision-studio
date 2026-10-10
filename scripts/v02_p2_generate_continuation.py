"""Single-scene local SVD continuation experiment; no original media overwritten."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request


def api(server, endpoint, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        server + endpoint, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)


def wait(server, prompt_id, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        record = api(server, "/history/" + prompt_id).get(prompt_id)
        if record:
            status = record.get("status", {})
            if status.get("status_str") == "error":
                raise RuntimeError("ComfyUI reported an execution error: " + str(status.get("messages", []))[-600:])
            if status.get("completed"):
                return record.get("outputs", {})
        time.sleep(3)
    raise TimeoutError("SVD continuation timed out")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="D:/AI-Video")
    p.add_argument("--scene", default="S006")
    p.add_argument("--server", default="http://127.0.0.1:8188")
    p.add_argument("--timeout", type=int, default=2400)
    args = p.parse_args()
    if not (len(args.scene) == 4 and args.scene.startswith("S") and args.scene[1:].isdigit() and 1 <= int(args.scene[1:]) <= 19):
        raise ValueError("Scene must be S001-S019")
    root = Path(args.root)
    server = args.server.rstrip("/")
    folder = root / "private" / "lost-signal" / "v0.2" / "p2" / "continuation" / args.scene
    source_frame = folder / "source_last_frame.png"
    if not source_frame.is_file():
        raise FileNotFoundError("Run v02_p2_prepare_continuation.py first")
    model = root / "ComfyUI" / "models" / "checkpoints" / "svd.safetensors"
    if not model.is_file():
        raise FileNotFoundError("SVD model not installed")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg not on PATH")
    input_dir = root / "ComfyUI" / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    input_name = "lost_signal_v02_p2_"+ args.scene + "_continuation_input.png"
    shutil.copy2(source_frame, input_dir / input_name)
    nodes = api(server, "/object_info")
    workflow = {
        "1": {"class_type": "ImageOnlyCheckpointLoader", "inputs": {"ckpt_name": "svd.safetensors"}},
        "2": {"class_type": "LoadImage", "inputs": {"image": input_name}},
        "3": {"class_type": "SVD_img2vid_Conditioning", "inputs": {"width": 1024, "height": 576, "video_frames": 14, "motion_bucket_id": 127, "fps": 6, "augmentation_level": 0, "clip_vision": ["1", 1], "init_image": ["2", 0], "vae": ["1", 2]}},
        "4": {"class_type": "VideoLinearCFGGuidance", "inputs": {"model": ["1", 0], "min_cfg": 1}},
        "5": {"class_type": "KSampler", "inputs": {"seed": 2026101600 + int(args.scene[1:]), "steps": 20, "cfg": 2.5, "sampler_name": "euler", "scheduler": "karras", "denoise": 1, "model": ["4", 0], "positive": ["3", 0], "negative": ["3", 1], "latent_image": ["3", 2]}},
        "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage", "inputs": {"filename_prefix": "lost_signal_v02_p2_" + args.scene + "_cont", "images": ["6", 0]}}
    }
    for node in workflow.values():
        kind = node["class_type"]
        if kind not in nodes:
            raise RuntimeError("ComfyUI node unavailable: " + kind)
        valid = set(nodes[kind].get("input", {}).get("required", {})) | set(nodes[kind].get("input", {}).get("optional", {}))
        if set(node["inputs"]) - valid:
            raise RuntimeError("Unsupported inputs on " + kind)
    result = api(server, "/prompt", {"prompt": workflow, "client_id": "emc-vision-studio-v02-p2"})
    prompt_id = result.get("prompt_id")
    if not prompt_id:
        raise RuntimeError("ComfyUI rejected continuation: " + str(result))
    outputs = wait(server, prompt_id, args.timeout)
    images = [image for value in outputs.values() for image in value.get("images", [])]
    if len(images) != 14:
        raise RuntimeError("Expected 14 output frames, got " + str(len(images)))
    frames_dir = folder / "generated_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    for index, item in enumerate(images):
        filename = item["filename"]
        subfolder = item.get("subfolder", "")
        source = root / "ComfyUI" / "output" / subfolder / filename
        if not source.is_file():
            raise FileNotFoundError(str(source))
        shutil.copy2(source, frames_dir / ("frame_%03d.png" % index))
    target = folder / (args.scene + "_continuation.mp4")
    temp = folder / (args.scene + "_continuation.tmp.mp4")
    subprocess.run(
        [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
         "-framerate", "6", "-i", str(frames_dir / "frame_%03d.png"),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", str(temp)],
        check=True
    )
    temp.replace(target)
    (folder / "generation_result.json").write_text(
        json.dumps({"status": "complete", "scene": args.scene, "frames": 14,
                    "fps": 6, "nominal_seconds": 14 / 6,
                    "prompt_id": prompt_id, "clip_name": target.name,
                    "note": "Experimental continuation; visual continuity not yet approved"},
                   ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("P2 CONTINUATION COMPLETE", args.scene)
    print("Frames: 14")
    print("Nominal seconds:", round(14 / 6, 3))
    print("Local clip:", target)
    print("Visual continuity must be reviewed before accepting this clip.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("P2 CONTINUATION ERROR:", type(error).__name__, str(error), file=sys.stderr)
        sys.exit(1)
