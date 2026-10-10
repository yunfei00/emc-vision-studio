import argparse
import copy
import json
import pathlib
import time
import urllib.request

def api(url, payload=None):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=40) as response:
        return json.load(response)

def wait(server, prompt_id, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        record = api(server + "/history/" + prompt_id).get(prompt_id)
        if record:
            status = record.get("status", {})
            for message in status.get("messages", []):
                if isinstance(message, list) and len(message) == 2 and message[0] == "execution_error":
                    detail = message[1]
                    raise RuntimeError("Node {} {}: {}".format(detail.get("node_id"), detail.get("node_type"), detail.get("exception_message")))
            if status.get("completed"):
                return record.get("outputs", {})
            if status.get("status_str") == "error":
                raise RuntimeError("ComfyUI execution failed")
        time.sleep(3)
    raise TimeoutError("Prompt timed out")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="D:/AI-Video")
    p.add_argument("--repo", required=True)
    p.add_argument("--server", default="http://127.0.0.1:8188")
    p.add_argument("--timeout", type=int, default=900)
    args = p.parse_args()
    root, repo = pathlib.Path(args.root), pathlib.Path(args.repo)
    plan = json.loads((repo / "plans" / "phase8_lost_signal_storyboard.json").read_text(encoding="utf-8"))
    workflow = json.loads((repo / "workflows" / "text-to-image" / "first-lab-sd15-api.json").read_text(encoding="utf-8"))
    model = "v1-5-pruned-emaonly.ckpt"
    if not (root / "ComfyUI" / "models" / "checkpoints" / model).is_file():
        raise FileNotFoundError("SD1.5 checkpoint not found")
    output = root / "private" / "lost-signal" / "phase8"
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"shots": {}}
    server = args.server.rstrip("/")
    for index, (scene, prompt) in enumerate(plan["new_shot_prompts"].items()):
        old = manifest["shots"].get(scene, {})
        if old.get("status") == "completed":
            existing = [root / "ComfyUI" / "output" / name for name in old.get("files", [])]
            if existing and all(path.is_file() for path in existing):
                print("SKIP", scene, flush=True)
                continue
        task = copy.deepcopy(workflow)
        task["1"]["inputs"]["ckpt_name"] = model
        task["2"]["inputs"]["text"] = prompt + ", photorealistic cinematic professional documentary, consistent clean RF laboratory, no readable text"
        task["3"]["inputs"]["text"] = plan["negative_prompt"]
        task["5"]["inputs"]["seed"] = 20262000 + index * 101
        task["7"]["inputs"]["filename_prefix"] = "lost_signal_phase8_" + scene
        print("GENERATING", scene, flush=True)
        try:
            queued = api(server + "/prompt", {"prompt": task, "client_id": "emc-vision-studio-phase8"})
            if "prompt_id" not in queued:
                raise RuntimeError("ComfyUI rejected request: " + str(queued))
            outputs = wait(server, queued["prompt_id"], args.timeout)
            filenames = [img["filename"] for item in outputs.values() for img in item.get("images", [])]
            if not filenames:
                raise RuntimeError("No images returned")
            manifest["shots"][scene] = {"status": "completed", "files": filenames, "seed": task["5"]["inputs"]["seed"]}
            print("COMPLETE", scene, flush=True)
        except Exception as exc:
            manifest["shots"][scene] = {"status": "failed", "error": str(exc)}
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            raise
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PHASE 8: ALL 13 NEW KEYFRAMES GENERATED LOCALLY", flush=True)

if __name__ == "__main__":
    main()
