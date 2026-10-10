import argparse
import hashlib
import pathlib
import sys
import urllib.request

URL = "https://huggingface.co/stabilityai/stable-video-diffusion-img2vid/resolve/main/svd.safetensors"
NAME = "svd.safetensors"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="D:/AI-Video")
    parser.add_argument("--url", default=URL)
    args = parser.parse_args()
    target = pathlib.Path(args.root) / "ComfyUI" / "models" / "checkpoints" / NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and target.stat().st_size > 1_000_000_000:
        print("MODEL EXISTS:", target)
        return
    partial = target.with_suffix(target.suffix + ".part")
    downloaded = partial.stat().st_size if partial.exists() else 0
    headers = {"User-Agent": "emc-vision-studio/phase5"}
    if downloaded:
        headers["Range"] = "bytes=" + str(downloaded) + "-"
    request = urllib.request.Request(args.url, headers=headers)
    print("Downloading public SVD model to LOCAL disk only:", target, flush=True)
    with urllib.request.urlopen(request, timeout=120) as response:
        status = response.status
        content_type = response.headers.get("Content-Type", "")
        if status == 206 and downloaded:
            mode = "ab"
        elif status == 200:
            mode = "wb"
            downloaded = 0
        else:
            raise RuntimeError("Unexpected HTTP status: " + str(status))
        if "text/html" in content_type:
            raise RuntimeError("Received HTML, not a model. Check license/login and model URL.")
        with partial.open(mode) as stream:
            while True:
                chunk = response.read(4 * 1024 * 1024)
                if not chunk:
                    break
                stream.write(chunk)
    if partial.stat().st_size < 1_000_000_000:
        raise RuntimeError("Downloaded file unexpectedly small. Check URL and authentication; partial file kept.")
    partial.replace(target)
    print("MODEL DOWNLOADED:", target, "bytes:", target.stat().st_size, flush=True)
    print("Restart ComfyUI after download.", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", e, file=sys.stderr)
        raise
