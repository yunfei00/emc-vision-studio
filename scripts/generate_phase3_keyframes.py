import argparse
import copy
import json
import pathlib
import time
import urllib.request
import urllib.error

SCENES = [
    ("S001", "Wide establishing shot of a modern EMC electronics test laboratory, realistic RF measurement instruments, smartphone on an anti static workbench, cinematic blue and neutral lighting, photorealistic professional documentary, 35mm lens, no readable text"),
    ("S002", "Close up of a modern smartphone on a clean electronics laboratory workbench, engineer hands nearby but not touching, realistic metallic and glass surfaces, cinematic shallow depth of field, photorealistic technical documentary, no logos, no readable text"),
    ("S003", "Over the shoulder shot of electronics engineer in a professional EMC test lab looking at a spectrum analyzer with abstract non readable waveform shapes, smartphone on bench, realistic cables and RF connectors, cinematic lighting, photorealistic"),
    ("S004", "Detailed cinematic close up of RF coaxial test cables and shielded measurement connectors beside a smartphone in a modern EMC laboratory, precise realistic materials, moody professional documentary, photorealistic, no labels"),
    ("S005", "Medium wide shot of electronics engineer methodically troubleshooting smartphone signal interference at RF measurement bench, spectrum analyzer and test instruments in background, realistic clean laboratory, cinematic corporate documentary, photorealistic"),
    ("S006", "Final cinematic hero shot of a smartphone on a clean RF laboratory test bench with measurement instruments softly blurred behind it, controlled neutral blue lighting, calm resolution mood, professional photorealistic film still, no text, no logos"),
]
NEGATIVE = "cartoon, anime, illustration, watermark, subtitles, readable text, logos, fake numbers, distorted hands, deformed fingers, broken smartphone, unrealistic connectors, low quality, blurry, duplicate objects"

def http_json(url, data=None):
    body = None if data is None else json.dumps(data).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)

def wait_for_prompt(server, prompt_id, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        record = http_json(server + "/history/" + prompt_id).get(prompt_id)
        if record:
            status = record.get("status", {})
            for message in status.get("messages", []):
                if isinstance(message, list) and len(message) == 2 and message[0] == "execution_error":
                    info = message[1]
                    raise RuntimeError("Node: {} {}\n{}\n{}".format(info.get("node_id"), info.get("node_type"), info.get("exception_message"), "".join(info.get("traceback", []))))
            if status.get("completed"):
                return record.get("outputs", {})
            if status.get("status_str") == "error":
                raise RuntimeError(json.dumps(status, ensure_ascii=False))
        time.sleep(3)
    raise TimeoutError("ComfyUI prompt timeout: " + prompt_id)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/AI-Video")
    parser.add_argument("--server", default="http://127.0.0.1:8188")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--model", default="v1-5-pruned-emaonly.ckpt")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    root = pathlib.Path(args.root)
    repo = pathlib.Path(args.repo)
    checkpoint = root / "ComfyUI" / "models" / "checkpoints" / args.model
    if not checkpoint.is_file():
        raise FileNotFoundError(str(checkpoint))
    workflow = json.loads((repo / "workflows" / "text-to-image" / "first-lab-sd15-api.json").read_text(encoding="utf-8"))
    private = root / "private" / "lost-signal" / "phase3"
    private.mkdir(parents=True, exist_ok=True)
    manifest_path = private / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest = {"project": "lost-signal", "scenes": {}}
    server = args.server.rstrip("/")
    for index, (scene_id, prompt) in enumerate(SCENES):
        if manifest["scenes"].get(scene_id, {}).get("status") == "completed":
            print("SKIP:", scene_id, "already completed", flush=True)
            continue
        task = copy.deepcopy(workflow)
        task["1"]["inputs"]["ckpt_name"] = args.model
        task["2"]["inputs"]["text"] = prompt
        task["3"]["inputs"]["text"] = NEGATIVE
        task["5"]["inputs"]["seed"] = 20261010 + index * 101
        task["7"]["inputs"]["filename_prefix"] = "lost_signal_phase3_" + scene_id
        print("START:", scene_id, flush=True)
        try:
            submitted = http_json(server + "/prompt", {"prompt": task, "client_id": "emc-vision-studio-local"})
            if "prompt_id" not in submitted:
                raise RuntimeError(json.dumps(submitted, ensure_ascii=False))
            outputs = wait_for_prompt(server, submitted["prompt_id"], args.timeout)
            filenames = [img.get("filename") for node in outputs.values() for img in node.get("images", [])]
            manifest["scenes"][scene_id] = {"status": "completed", "seed": task["5"]["inputs"]["seed"], "prompt": prompt, "prompt_id": submitted["prompt_id"], "files": filenames}
            print("DONE:", scene_id, filenames, flush=True)
        except Exception as exc:
            manifest["scenes"][scene_id] = {"status": "failed", "error": str(exc)}
            print("FAILED:", scene_id, str(exc), flush=True)
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            raise
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("ALL SCENES COMPLETED. Files remain LOCAL:", root / "ComfyUI" / "output", flush=True)
    print("Private manifest:", manifest_path, flush=True)

if __name__ == "__main__":
    main()
