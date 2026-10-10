import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import time
import urllib.request

SCENES = ["S001", "S002", "S003", "S004", "S005", "S006"]

def api(url, data=None):
    body = None if data is None else json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.load(response)

def wait(server, prompt_id, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        record = api(server + "/history/" + prompt_id).get(prompt_id)
        if record:
            status = record.get("status", {})
            for event in status.get("messages", []):
                if isinstance(event, list) and len(event) == 2 and event[0] == "execution_error":
                    info = event[1]
                    raise RuntimeError("FAILED NODE {} {}: {}".format(info.get("node_id"), info.get("node_type"), info.get("exception_message")))
            if status.get("completed"):
                return record.get("outputs", {})
            if status.get("status_str") == "error":
                raise RuntimeError("ComfyUI execution error")
        time.sleep(3)
    raise TimeoutError("Prompt timed out: " + prompt_id)

def render_scene(root, private, server, nodes, scene, timeout, ffmpeg):
    candidates = sorted((root / "ComfyUI" / "output").glob("lost_signal_phase3_" + scene + "_*.png"))
    if not candidates:
        raise FileNotFoundError("No image for " + scene)
    source = candidates[-1]
    name = "lost_signal_phase6_" + scene + "_input.png"
    shutil.copy2(source, root / "ComfyUI" / "input" / name)
    workflow = {
        "1": {"class_type": "ImageOnlyCheckpointLoader", "inputs": {"ckpt_name": "svd.safetensors"}},
        "2": {"class_type": "LoadImage", "inputs": {"image": name}},
        "3": {"class_type": "SVD_img2vid_Conditioning", "inputs": {"width": 1024, "height": 576, "video_frames": 14, "motion_bucket_id": 127, "fps": 6, "augmentation_level": 0, "clip_vision": ["1", 1], "init_image": ["2", 0], "vae": ["1", 2]}},
        "4": {"class_type": "VideoLinearCFGGuidance", "inputs": {"model": ["1", 0], "min_cfg": 1}},
        "5": {"class_type": "KSampler", "inputs": {"seed": 20261010 + int(scene[1:]) * 101, "steps": 20, "cfg": 2.5, "sampler_name": "euler", "scheduler": "karras", "denoise": 1, "model": ["4", 0], "positive": ["3", 0], "negative": ["3", 1], "latent_image": ["3", 2]}},
        "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage", "inputs": {"filename_prefix": "lost_signal_phase6_" + scene, "images": ["6", 0]}}
    }
    for node in workflow.values():
        valid = set(nodes[node["class_type"]].get("input", {}).get("required", {})) | set(nodes[node["class_type"]].get("input", {}).get("optional", {}))
        unknown = set(node["inputs"]) - valid
        if unknown:
            raise RuntimeError("Unsupported node inputs: {} {}".format(node["class_type"], sorted(unknown)))
    result = api(server + "/prompt", {"prompt": workflow, "client_id": "emc-vision-studio-phase6"})
    if "prompt_id" not in result:
        raise RuntimeError("ComfyUI rejected scene {}: {}".format(scene, result))
    outputs = wait(server, result["prompt_id"], timeout)
    names = [item["filename"] for value in outputs.values() for item in value.get("images", [])]
    if len(names) != 14:
        raise RuntimeError("{}: expected 14 frames, got {}".format(scene, len(names)))
    frames_dir = private / scene
    frames_dir.mkdir(parents=True, exist_ok=True)
    for index, filename in enumerate(names):
        frame = root / "ComfyUI" / "output" / filename
        if not frame.is_file():
            raise FileNotFoundError(str(frame))
        shutil.copy2(frame, frames_dir / ("frame_%03d.png" % index))
    clip = private / (scene + ".mp4")
    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                    "-framerate", "6", "-i", str(frames_dir / "frame_%03d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                    str(clip)], check=True)
    return {"status": "completed", "input": str(source), "clip": str(clip), "prompt_id": result["prompt_id"], "frames": 14}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="D:/AI-Video")
    p.add_argument("--server", default="http://127.0.0.1:8188")
    p.add_argument("--timeout", type=int, default=2400)
    args = p.parse_args()
    root = pathlib.Path(args.root)
    private = root / "private" / "lost-signal" / "phase6"
    private.mkdir(parents=True, exist_ok=True)
    manifest_file = private / "manifest.json"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8")) if manifest_file.exists() else {"scenes": {}}
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not in PATH")
    if not (root / "ComfyUI" / "models" / "checkpoints" / "svd.safetensors").is_file():
        raise FileNotFoundError("SVD checkpoint not found")
    server = args.server.rstrip("/")
    nodes = api(server + "/object_info")
    required = ["ImageOnlyCheckpointLoader", "LoadImage", "SVD_img2vid_Conditioning", "VideoLinearCFGGuidance", "KSampler", "VAEDecode", "SaveImage"]
    if any(node not in nodes for node in required):
        raise RuntimeError("Missing SVD nodes")
    for scene in SCENES:
        clip = private / (scene + ".mp4")
        if manifest["scenes"].get(scene, {}).get("status") == "completed" and clip.is_file() and clip.stat().st_size > 0:
            print("SKIP", scene, "already complete", flush=True)
            continue
        print("GENERATING", scene, flush=True)
        try:
            manifest["scenes"][scene] = render_scene(root, private, server, nodes, scene, args.timeout, ffmpeg)
            print("COMPLETE", scene, flush=True)
        except Exception as exc:
            manifest["scenes"][scene] = {"status": "failed", "error": str(exc)}
            manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            raise
        manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    playlist = private / "clips.txt"
    playlist.write_text("".join("file '{}.mp4'\n".format(scene) for scene in SCENES), encoding="utf-8")
    final = private / "lost_signal_phase6_svd_preview.mp4"
    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "concat",
                    "-safe", "0", "-i", str(playlist), "-c", "copy", str(final)], cwd=str(private), check=True)
    print("ALL SIX AI VIDEO CLIPS COMPLETE", flush=True)
    print("LOCAL VIDEO:", final, flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PHASE 6 FAILED:", exc, file=sys.stderr, flush=True)
        sys.exit(1)
