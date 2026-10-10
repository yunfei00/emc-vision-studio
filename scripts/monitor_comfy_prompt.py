import argparse
import json
import time
import urllib.error
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument("--server", default="http://127.0.0.1:8188")
parser.add_argument("--prompt-id", required=True)
parser.add_argument("--timeout", type=int, default=600)
args = parser.parse_args()
url = args.server.rstrip("/") + "/history/" + args.prompt_id
deadline = time.monotonic() + args.timeout
while time.monotonic() < deadline:
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            history = json.load(response)
    except (urllib.error.URLError, TimeoutError) as exc:
        print("HISTORY REQUEST ERROR:", exc, flush=True)
        time.sleep(3)
        continue
    result = history.get(args.prompt_id)
    if result:
        status = result.get("status", {})
        print("PROMPT STATUS:", status.get("status_str", "unknown"), flush=True)
        for message in status.get("messages", []):
            if isinstance(message, (list, tuple)) and len(message) > 1:
                kind, details = message[0], message[1]
                if kind == "execution_error":
                    print("FAILED NODE:", details.get("node_id"), details.get("node_type"), flush=True)
                    print("EXCEPTION:", details.get("exception_type"), details.get("exception_message"), flush=True)
                    print("TRACEBACK:", flush=True)
                    for line in details.get("traceback", []):
                        print(line, flush=True)
                    raise SystemExit(2)
        if status.get("completed"):
            print("GENERATION COMPLETE. Outputs:", json.dumps(result.get("outputs", {}), ensure_ascii=False), flush=True)
            raise SystemExit(0)
        if status.get("status_str") == "error":
            print("ERROR DETAILS:", json.dumps(status, ensure_ascii=False, indent=2), flush=True)
            raise SystemExit(2)
    time.sleep(3)
print("TIMEOUT: check ComfyUI console and task history.", flush=True)
raise SystemExit(3)
