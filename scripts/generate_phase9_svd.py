import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import time
import urllib.request

def api(url, payload=None):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as res:
        return json.load(res)

def wait(server, prompt_id, timeout):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        record = api(server + "/history/" + prompt_id).get(prompt_id)
        if record:
            status = record.get("status", {})
            for event in status.get("messages", []):
                if isinstance(event, list) and len(event) == 2 and event[0] == "execution_error":
                    info = event[1]
                    raise RuntimeError("NODE {} {}: {}".format(info.get("node_id"), info.get("node_type"), info.get("exception_message")))
            if status.get("completed"):
                return record.get("outputs", {})
            if status.get("status_str") == "error":
                raise RuntimeError("ComfyUI execution error")
        time.sleep(3)
    raise TimeoutError("Prompt timed out: " + prompt_id)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="D:/AI-Video")
    p.add_argument("--server", default="http://127.0.0.1:8188")
    p.add_argument("--timeout", type=int, default=2400)
    args = p.parse_args()
    root = pathlib.Path(args.root)
    output = root / "private" / "lost-signal" / "phase9"
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"shots": {}}
    server = args.server.rstrip("/")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg not in PATH")
    if not (root / "ComfyUI" / "models" / "checkpoints" / "svd.safetensors").is_file():
        raise FileNotFoundError("SVD model not installed")
    nodes = api(server + "/object_info")
    required = ["ImageOnlyCheckpointLoader", "LoadImage", "SVD_img2vid_Conditioning", "VideoLinearCFGGuidance", "KSampler", "VAEDecode", "SaveImage"]
    if any(key not in nodes for key in required):
        raise RuntimeError("Missing required SVD nodes")
    for index in range(7, 20):
        scene = "S%03d" % index
        clip = output / (scene + ".mp4")
        if manifest["shots"].get(scene, {}).get("status") == "complete" and clip.is_file() and clip.stat().st_size > 0:
            print("SKIP", scene, flush=True)
            continue
        images = sorted((root / "ComfyUI" / "output").glob("lost_signal_phase8_" + scene + "_*.png"))
        if not images:
            raise FileNotFoundError("Missing keyframe for " + scene)
        name = "lost_signal_phase9_" + scene + "_input.png"
        shutil.copy2(images[-1], root / "ComfyUI" / "input" / name)
        workflow = {
            "1": {"class_type": "ImageOnlyCheckpointLoader", "inputs": {"ckpt_name": "svd.safetensors"}},
            "2": {"class_type": "LoadImage", "inputs": {"image": name}},
            "3": {"class_type": "SVD_img2vid_Conditioning", "inputs": {"width": 1024, "height": 576, "video_frames": 14, "motion_bucket_id": 127, "fps": 6, "augmentation_level": 0, "clip_vision": ["1", 1], "init_image": ["2", 0], "vae": ["1", 2]}},
            "4": {"class_type": "VideoLinearCFGGuidance", "inputs": {"model": ["1", 0], "min_cfg": 1}},
            "5": {"class_type": "KSampler", "inputs": {"seed": 20262000 + index * 101, "steps": 20, "cfg": 2.5, "sampler_name": "euler", "scheduler": "karras", "denoise": 1, "model": ["4", 0], "positive": ["3", 0], "negative": ["3", 1], "latent_image": ["3", 2]}},
            "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
            "7": {"class_type": "SaveImage", "inputs": {"filename_prefix": "lost_signal_phase9_" + scene, "images": ["6", 0]}}
        }
        print("GENERATING", scene, flush=True)
        try:
            result = api(server + "/prompt", {"prompt": workflow, "client_id": "emc-vision-studio-phase9"})
            if "prompt_id" not in result:
                raise RuntimeError("ComfyUI rejected request: " + str(result))
            outputs = wait(server, result["prompt_id"], args.timeout)
            names = [image["filename"] for node in outputs.values() for image in node.get("images", [])]
            if len(names) != 14:
                raise RuntimeError("Expected 14 frames, got {}".format(len(names)))
            frames_dir = output / scene
            frames_dir.mkdir(parents=True, exist_ok=True)
            for n, filename in enumerate(names):
                source = root / "ComfyUI" / "output" / filename
                if not source.is_file():
                    raise FileNotFoundError(str(source))
                shutil.copy2(source, frames_dir / ("frame_%03d.png" % n))
            subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-framerate", "6",
                            "-i", str(frames_dir / "frame_%03d.png"), "-c:v", "libx264",
                            "-pix_fmt", "yuv420p", "-crf", "20", str(clip)], check=True)
            manifest["shots"][scene] = {"status": "complete", "clip": str(clip), "frames": 14}
            print("COMPLETE", scene, flush=True)
        except Exception as exc:
            manifest["shots"][scene] = {"status": "failed", "error": str(exc)}
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            raise
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PHASE 9 ALL 13 AI CLIPS COMPLETE", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PHASE 9 ERROR:", exc, file=sys.stderr, flush=True)
        sys.exit(1)
