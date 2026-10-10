"""Resumable, bounded, local-only weekend SVD continuation queue."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request


def write(path, obj):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def run(cmd, timeout):
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout)[-1200:] or "Subprocess failed")
    return result.stdout


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="D:/AI-Video")
    p.add_argument("--server", default="http://127.0.0.1:8188")
    p.add_argument("--max-scenes", type=int, default=19)
    p.add_argument("--min-free-gb", type=int, default=25)
    p.add_argument("--timeout", type=int, default=2400)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    if not 1 <= args.max_scenes <= 19 or args.min_free_gb < 5 or args.timeout < 60:
        raise ValueError("Invalid safety limits")
    root = Path(args.root)
    base = root / "private" / "lost-signal"
    out = base / "v0.2" / "p2"
    plan = json.loads((out / "motion_extension_plan.json").read_text(encoding="utf-8"))
    scenes = plan["priority_order"][:args.max_scenes]
    if args.dry_run:
        print("DRY RUN:", ", ".join(x["scene"] for x in scenes))
        print("No files or GPU tasks started.")
        return
    if not (root / "ComfyUI" / "models" / "checkpoints" / "svd.safetensors").is_file():
        raise FileNotFoundError("Missing existing SVD model")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg missing")
    with urllib.request.urlopen(args.server.rstrip("/") + "/object_info", timeout=20) as response:
        if response.status != 200:
            raise RuntimeError("ComfyUI unavailable")
    queue = out / "weekend_queue"
    queue.mkdir(parents=True, exist_ok=True)
    lock = queue / "running.lock"
    try:
        fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise RuntimeError("Queue lock exists. Check if another queue is running before removing it.")
    os.close(fd)
    report_path = queue / "report.json"
    report = {"started": datetime.now().isoformat(), "status": "running", "shots": {}}
    try:
        for item in scenes:
            scene = item["scene"]
            folder = out / "continuation" / scene
            target = folder / (scene + "_continuation.mp4")
            if (queue / "STOP").exists():
                report["status"] = "stopped_by_user"
                break
            if target.is_file() and target.stat().st_size > 1000:
                report["shots"][scene] = {"status": "skipped_existing"}
                write(report_path, report)
                continue
            if shutil.disk_usage(str(root)).free < args.min_free_gb * 1024 ** 3:
                report["status"] = "stopped_low_disk"
                break
            try:
                source = base / ("phase6" if int(scene[1:]) <= 6 else "phase9") / (scene + ".mp4")
                if not source.is_file():
                    raise FileNotFoundError(str(source))
                folder.mkdir(parents=True, exist_ok=True)
                frame = folder / "source_last_frame.png"
                if not frame.is_file() or frame.stat().st_size == 0:
                    run([ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                         "-i", str(source), "-an", "-vf", "reverse",
                         "-frames:v", "1", "-update", "1", str(frame)], 180)
                if not frame.is_file() or frame.stat().st_size == 0:
                    raise RuntimeError("No last frame extracted")
                script = Path(__file__).with_name("v02_p2_generate_continuation.py")
                output = run([sys.executable, str(script), "--root", str(root),
                              "--scene", scene, "--server", args.server,
                              "--timeout", str(args.timeout)], args.timeout + 180)
                report["shots"][scene] = {"status": "generated_pending_visual_review",
                                           "detail": output[-300:]}
            except Exception as error:
                report["shots"][scene] = {"status": "failed", "error": str(error)[-900:]}
            write(report_path, report)
        if report["status"] == "running":
            report["status"] = "finished_pending_visual_review"
    finally:
        report["finished"] = datetime.now().isoformat()
        write(report_path, report)
        lock.unlink(missing_ok=True)
    print("WEEKEND QUEUE:", report["status"])
    print("Generated:", sum(x["status"] == "generated_pending_visual_review" for x in report["shots"].values()))
    print("Failed:", sum(x["status"] == "failed" for x in report["shots"].values()))
    print("Report:", report_path)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("WEEKEND QUEUE ERROR:", type(error).__name__, str(error), file=sys.stderr)
        sys.exit(1)
